import os
from utils import read_file
from schema import InsertCountryCode
from langchain_openai import AzureChatOpenAI
from langchain.agents import (
    create_react_agent, 
    AgentExecutor
)
from langchain.tools import Tool
from langchain_core.prompts import PromptTemplate
from crawler.cwa import Cwa
from dotenv import load_dotenv

cwa_obj = Cwa()
load_dotenv()
get_env = os.getenv
model = AzureChatOpenAI(
    temperature=0.9,   
    api_key=get_env('API_KEY'),
    openai_api_version=get_env('OPENAI_API_VERSION'),
    azure_deployment=get_env('AZURE_DEPLOYMENT'),
    azure_endpoint=get_env('AZURE_ENDPOINT'),
)

template = read_file('prompt.txt')
prompt = PromptTemplate.from_template(template)


get_country_code_tool = Tool.from_function(
    name = '取得城市代碼',
    description = 'Use this tool can find out the country code',
    func=cwa_obj.get_country_mapping_code,
)

get_weather_tool = Tool.from_function(
    name = '取得天氣資訊',
    description = 'Use this tool can get the weather information',
    args_schema=InsertCountryCode,
    func=cwa_obj.get_weather_response,
)

tools = [get_country_code_tool, get_weather_tool]

agent = create_react_agent(
    tools=tools,
    llm=model,
    prompt=prompt,
)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
response = agent_executor.invoke({"input": "請告訴我新莊區今日天氣如何?"})
print(response)