import operator
import functools
import pandas as pd
from loguru import logger
from langchain.tools import tool
from sqlalchemy.orm import Session
from langgraph.graph import StateGraph, END
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import PromptTemplate
from typing_extensions import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage, AIMessage
from langgraph.prebuilt import ToolInvocation, ToolExecutor
from langchain_community.callbacks import get_openai_callback
from crawl import Cwa
from fuzzywuzzy.process import extractOne
from datetime import datetime


cwa_obj = Cwa()

class MyState(TypedDict):
    question: BaseMessage
    messages: Annotated[Sequence[BaseMessage], operator.add]
    payload: dict
    

@tool
def get_country_weather(code, date):
    """Use the country code to get the weather
    date="mm/dd, mm/dd"
    """
    output = []
    response = cwa_obj.get_weather_response(code)
    date_list = date.split(',')
    for date in date_list:
        data = response[response['時間'].str.contains(date)]
        output.append(data)
    return output

@tool
def get_country_code(countryList:str):
    """use the countryList to find the country code
    countryList="xx,xx,xx"
    """
    _mapping = {}
    response = cwa_obj.get_country_mapping_code()
    mapping_list = list(response.keys())
    for country in countryList.split(','):
        real_country, score = extractOne(country, mapping_list)
        country_code = response.get(real_country)
        _mapping[country_code] = real_country
    return _mapping


class WeatherAgent:
    def __init__(self, session, model):
        self.session:Session = session
        self.model = model
        self.workflow = StateGraph(MyState)
    
    def create_agent(
        self,
        model, 
        prompt=''
    ):
        prompt_template = PromptTemplate.from_template(
            prompt,
        )
        chain = (
            prompt_template | model
        )
        return chain

    def create_tool_agent(
        self, 
        model:AzureChatOpenAI, 
        tools, 
        prompt
    ):
        prompt_template = PromptTemplate.from_template(
            prompt,
        )
        llm_bind_with_tool = model.bind_tools(tools)
        chain = (
            prompt_template | llm_bind_with_tool
        )
        return chain

    def agent_node(self, state, agent):
        messages = state['messages']
        payload = state['payload']
        last_message = messages[-1] if messages else ''
        question = state['question'][-1]
        response = agent.invoke(
            {
                'messages':last_message,
                'question':question,
                'payload':payload
            },
        )
        return {
            'messages': [response.content]
        }

    def tool_agent_node(self, state, agent):
        output = []
        messages = state['messages']
        question = state['question'][-1]
        payload = state['payload']
        last_message = messages[-1] if messages else ''
        response = agent.invoke({
            'messages':last_message,
            'payload':payload,
            'question':question
        })
        logger.info(response)
        tool_infos = response.tool_calls
        for tool_info in tool_infos:
            output.append(
                AIMessage(
                    content='',
                    name=tool_info.get('name'),
                    args=tool_info.get('args'),
                    tool_call_id=tool_info.get('id')
                )
            )
        return {
            'messages': [output],
        }

    def tool_node(self, state):
        output = {}
        tool_execute = ToolExecutor(
            [
                get_country_weather, 
                get_country_code
            ]
        )
        messages = state.get('messages')
        tool_infos = messages[-1]
        for tool_info in tool_infos:
            tool_call_id = tool_info.tool_call_id
            tool_name = tool_info.name
            tool_args = tool_info.args
            action = ToolInvocation(
                tool=tool_name,
                tool_input=tool_args
            )
            response = tool_execute.invoke(action)
            if tool_name == 'get_country_code':
                output.update(response)
            elif tool_name == 'get_country_weather':
                if isinstance(response, pd.DataFrame):
                    response = response.to_dict(orient='records')
                output.update({tool_args.get('code'):response})
        if tool_name == 'get_country_code':
            return {'payload':output}
        return {'messages':[
            ToolMessage(
                    [str(output)], 
                    tool_call_id=tool_call_id,
                    name=tool_name
                )
            ]
        }

    def should_continue(self, state):
        messages = state['messages']
        last_message = messages[-1]
        if isinstance(last_message, list):
            last_message = last_message[0]
        tool_name = last_message.name
        if tool_name == 'get_country_code':
            return 'continue'
        else:
            return 'end'

    def create_node(self, tools=[], prompt=''):
        if tools:
            node = functools.partial(
                self.tool_agent_node, 
                agent=self.create_tool_agent(
                    model=self.model,
                    tools=tools,
                    prompt=prompt
                )
            )
        else:
            node = functools.partial(
                self.agent_node,
                agent=self.create_agent(
                    model=self.model,
                    prompt=prompt
                )
            )
        return node

    def set_workflow(self):
        self.workflow.add_node(
            'find_country_code_node', 
            self.create_node(
                tools=[get_country_code], 
                prompt='''
                    找出 {question} 中的台灣地區，若有多個地區用","區隔。並轉換為代號
                ''')
        )
        
        self.workflow.add_node(
            'get_weather_node', 
            self.create_node(
                tools=[get_country_weather], 
                prompt=f'今日日期為{datetime.now()}' + '''
                        找出{question}中的日期並轉換格式為"mm/dd"，若有多個日期用","區隔，ex"mm/dd,mm/dd"。
                        根據{payload}中的數字以及{question}中的日期找出對應的天氣資訊。
                    '''
                )
        )
        self.workflow.add_node('tool_node', self.tool_node)
        self.workflow.add_node(
            'summary_node', 
            self.create_node(
                prompt='''
                    你是個氣象播報員。
                    你獲得了天氣資訊{messages}用以回答User的問題:{question}。
                    若{messages}為空請告知找不到，並且不要顯示其他天氣資訊。
                    若有則用天氣預報的方式各別回覆不同城市不同日期的"地區、日期、最高溫度、最低溫度、天氣狀況、降雨機率"。
                    其中若含有地區代號(7位數字)，幫我轉成地區。
                '''
        ))

        self.workflow.add_edge('find_country_code_node', 'tool_node')
        self.workflow.add_conditional_edges(
            'tool_node', 
            self.should_continue,
            {
                'continue': 'get_weather_node',
                'end': 'summary_node',
            }
        )
        self.workflow.add_edge('get_weather_node', 'tool_node')
        self.workflow.add_edge('summary_node', END)
        self.workflow.set_entry_point('find_country_code_node')
        
    def run(self, question):
        self.set_workflow()
        app = self.workflow.compile()
        with get_openai_callback() as cb:
            response = app.invoke(
                {
                    'question': [
                        HumanMessage(question)
                    ]
                }
            )
        return response.get('messages')[-1]


async def app(**kwargs):
    session = kwargs.get("postgre_session")
    question = kwargs.get("question")
    model = kwargs.get("_model")
    obj = WeatherAgent(session, model)
    message = obj.run(question)
    return message, [], {}

