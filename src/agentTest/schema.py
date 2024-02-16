from langchain_core.pydantic_v1 import BaseModel


class CwaSchema(BaseModel):
    country:str