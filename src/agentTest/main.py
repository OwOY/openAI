from config import (
    API_KEY,
    OPENAI_API_VERSION,
    AZURE_DEPLOYMENT,
    AZURE_ENDPOINT
)
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

cwa_obj = Cwa()

model = AzureChatOpenAI(
    temperature=0,   
    api_key=API_KEY,
    openai_api_version=OPENAI_API_VERSION,
    azure_deployment=AZURE_DEPLOYMENT,
    azure_endpoint=AZURE_ENDPOINT
)

template = read_file('prompt.txt')
prompt = PromptTemplate.from_template(template)

_from_tool = Tool.from_function

tools = [
    _from_tool(
        name = '取得城市代碼',
        description = 'Use this tool can find out the country code',
        func=cwa_obj.get_country_mapping_code,
    ), 
    _from_tool(
        name = '取得天氣資訊',
        description = 'Use this tool can get the weather information',
        args_schema=InsertCountryCode,
        func=cwa_obj.get_weather_response,
    )
]

agent = create_react_agent(
    tools=tools,
    llm=model,
    prompt=prompt,
)
agent_executor = AgentExecutor(
    agent=agent, 
    tools=tools, 
    verbose=True, 
    handle_parsing_errors=True,
)
response = agent_executor.invoke(
    {"input": "請問今天淡水區禮拜日的天氣如何?"}
)

print(response)