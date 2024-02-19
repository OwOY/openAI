<img src='img/OpenAI_Logo_(2).svg.png'>

---
<br>
<br>
<br>

## How to use OpenAI
- AzureChatOpenAI  
設定model參數

```
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
    讓Agent根據先前的思考進行行動，並從該行動的結果中獲得觀察，形成 **思考→行動→觀察** 的流程
    [Thought]–>[Action]–>[Observation]
   - [sample_prompt.txt](src/agentTest/prompt.txt)
3. 執行主程式
   - [main.py](src/agentTest/main.py)


<br>
<br>
<br>

# 參考資料
[LLM Agents如何執行任務](https://hackmd.io/@YungHuiHsu/rkK52BkQp?utm_source=preview-mode&utm_medium=rec)