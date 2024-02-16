import os
from utils import read_file
from schema import CwaSchema
from langchain_openai import AzureChatOpenAI
from langchain.agents import (
    create_react_agent, 
    AgentExecutor
)
from langchain.tools import Tool
from langchain_core.prompts import PromptTemplate
from crawler.cwa import Cwa
from dotenv import load_dotenv

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

crawl_tool = Tool.from_function(
    name = '天氣預報',
    description = '取得中央氣象局資料，用以取得本周天氣資料',
    args_schema=CwaSchema,
    func=Cwa().main,
)

tools = [crawl_tool]

agent = create_react_agent(
    tools=tools,
    llm=model,
    prompt=prompt,
)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
response = agent_executor.invoke({"input": "請告訴我新北市板橋區今日天氣如何?"})
print(response)