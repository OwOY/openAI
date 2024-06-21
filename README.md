<p align='center'>
    <img src='img/OpenAI_Logo_(2).svg.png' width="300px">
</p>


# How to use OpenAI
- AzureChatOpenAI  
    設定model參數

    ```python
    from langchain_openai import AzureChatOpenAI
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
    ```


### Agent
[Sample Project](src/agentTest)  
#### Step
1. 建立工具  
    客製化工具，讓Agent可以使用這些工具進行思考
   - [cwa.py](src/agentTest/crawler/cwa.py)  

    工具參數
   - [schema.py](src/agentTest/schema.py)  
2. 創建文本  
    - [sample_prompt.txt](src/agentTest/prompt.txt)  

    讓Agent根據先前的思考進行行動，並從該行動的結果中獲得觀察，形成 **思考→行動→觀察** 的流程    
    [Thought]–>[Action]–>[Observation]  

    並遵循以下六大策略：  
      1. 寫出清晰的指令  
      2. 提供參考文本  
      3. 將複雜的任務拆分為更簡單的子任務  
      4. 給模型時間「思考」  
      5. 使用外部工具  
      6. 系統地測試變更  

3. 執行主程式
   - [main.py](src/agentTest/main.py)


<br>
<br>
<br>

## LangGraph

LangGraph作為一個新的庫，用來加強和改進RAG（Retrieval-Augmented Generation）管線。以下比較了使用LangGraph之前和之後的RAG管線的優缺點，並具體舉例說明不同之處。

與傳統RAG管線相比
- 優點：  
    - 線性流程，簡單易懂
    - 直接由查詢導向檔案的檢索，再生成回覆

- 缺點：
    - 缺少回饋迴路，如果初始檢索的結果不理想，管線缺乏機制重新評估問題或改進查詢  
    - 達成單一流向，無法進行迭代最佳化  
    - 在復雜或需要多次檢索才能找到最佳解答的場景中，效率低下  

### Install
```
python -m pip install langgraph
```
### Step
1. 設立MyState類，傳輸資料
    ```python
    from langchain_core.messages import BaseMessage
    from typing import TypedDict, Sequence, Annotated
    from langchain_core
    import operator

    class MyState(TypedDict):
        question: BaseMessage
        messages: Annotated[Sequence[BaseMessage], operator.add]
        payload: dict
    ```
2. 準備工具
    ```python
    from langchain.tools import tool
    
    @tool
    def add(a, b):
        return a + b
    
    ```
3. 創建一個新的node
    ```python
    from langchain_core.messages import BaseMessage
    from functools import partial
    from langchain_core.prompts import PromptTemplate
    from langchain_core.tools import ToolExecutor

    def create_agent(state, tools, prompt):
        messages = state['question']
        prompt = PromptTemplate(prompt)
        llm_bind_tool = llm.bind_tools(tools)
        chain = prompt | llm_bind_tool
        response = chain.invoke(messages[-1])
        return response

    def create_node(state):
        node = functools.partial(
            create_agent, 
            tools=[add],
            prompt='you are a calculator. ...'
        )
        return node

    def tool_node(state):
        tool_execute = ToolExecutor([add])
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

    ```
4. 準備條件
    - 條件判斷是否繼續執行(可根據使用狀況調整)
    ```python
    from langchain_core.messages import BaseMessage

    def should_continue(state):
        messages = state['messages']
        last_message = messages[-1].content
        if last_message == 'end':
            return 'end'
        else:
            return 'tool'

    ```
4. 建立graph路徑
    - edge: 連接兩個node
    - conditional edge: 有條件的連接兩個node
    - entry point: 設定起始點

    ```python
    from langgraph.graph import END, StateGraph

    workflow = StateGraph(MyState)

    workflow.add_node('agent', create_node)
    workflow.add_node('tool', tool_node)

    workflow.add_edge('agent', 'tool')
    workflow.add_edge('tool', END)

    workflow.add_conditional_edges(
        'agent',
        should_continue,
        {
            'tool': 'tool',
            'end': END
        }
    )
    workflow.set_entry_point('agent')
    ```
5. 執行
    ```python
    app = workflow.compile()
    response = app.invoke({
        'question':[HumanMessage('What is 1+1?')]
    })
    ```
    > 2



# 參考資料
- [LLM Agents如何執行任務](https://hackmd.io/@YungHuiHsu/rkK52BkQp?utm_source=preview-mode&utm_medium=rec)  
- [langgraph可重新評估、改進、迭代，資料來源品質或格式不穩定時特別能提高回答品質](https://medium.com/@bohachu/langgraph%E5%8F%AF%E9%87%8D%E6%96%B0%E8%A9%95%E4%BC%B0-%E6%94%B9%E9%80%B2-%E8%BF%AD%E4%BB%A3-%E8%B3%87%E6%96%99%E4%BE%86%E6%BA%90%E5%93%81%E8%B3%AA%E6%88%96%E6%A0%BC%E5%BC%8F%E4%B8%8D%E7%A9%A9%E5%AE%9A%E6%99%82%E7%89%B9%E5%88%A5%E8%83%BD%E6%8F%90%E9%AB%98%E5%9B%9E%E7%AD%94%E5%93%81%E8%B3%AA-93470ae7f1f1)