from langchain_core.pydantic_v1 import BaseModel


class MappingCode(BaseModel):
    country:str

class InsertCountryCode(BaseModel):
    code:str