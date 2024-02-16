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


## Agent
[Sample Project](src/agentTest)  


# 待補充