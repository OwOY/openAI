from dotenv import load_dotenv
import os

load_dotenv()

get_env = os.getenv

API_KEY = get_env('API_KEY')
OPENAI_API_VERSION = get_env('OPENAI_API_VERSION')
AZURE_DEPLOYMENT = get_env('AZURE_DEPLOYMENT')
AZURE_ENDPOINT = get_env('AZURE_ENDPOINT')