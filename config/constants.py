import os
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
load_dotenv("environment.env")

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
MODEL_NAME = "gemini-2.0-flash-lite"

llm = ChatGoogleGenerativeAI(model=MODEL_NAME, temperature=0, google_api_key=GEMINI_API_KEY)