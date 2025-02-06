from langchain_ollama import OllamaEmbeddings

from langchain_core.vectorstores import InMemoryVectorStore



def get_embedding_text(text: str) -> str:
    if text == 'ollama3':
        embeddings = OllamaEmbeddings(model="llama3")

        return embeddings

