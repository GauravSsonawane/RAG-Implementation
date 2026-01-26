from langchain_ollama import ChatOllama
import os
from dotenv import load_dotenv

load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

# User mentioned GPT-120B via Ollama. 
# We'll use llama3 or the specific model tag if known. 
# For demonstration, we'll use a configurable model name.
MODEL_NAME = os.getenv("OLLAMA_MODEL", "gpt-oss:120b-cloud")

def get_llm():
    return ChatOllama(
        model=MODEL_NAME,
        base_url=OLLAMA_URL,
        temperature=0,
    )
