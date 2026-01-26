from langchain_ollama import OllamaEmbeddings
import asyncio

async def test():
    try:
        print("Testing Ollama embeddings...")
        embeddings = OllamaEmbeddings(
            model="nomic-embed-text:latest",
            base_url="http://localhost:11434"
        )
        # Try to embed a simple string
        res = await embeddings.aembed_query("test")
        print(f"Success! Embedding size: {len(res)}")
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test())
