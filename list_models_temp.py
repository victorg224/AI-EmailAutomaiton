from google.genai import Client, types
import os
from dotenv import load_dotenv

load_dotenv()

client = Client(
    api_key=os.getenv("GOOGLE_API_KEY"),
    http_options=types.HttpOptions(api_version="v1")
)

models = client.models.list()
for model in models:
    if 'generateContent' in model.supported_actions:
        print(f"{model.name} | Supports: {model.supported_actions}") 