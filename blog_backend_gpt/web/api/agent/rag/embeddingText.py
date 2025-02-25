from langchain_ollama import OllamaEmbeddings

from langchain_huggingface import HuggingFaceEmbeddings

def get_embedding_text(text: str) -> str:
    if text == 'ollama3':
        import os
        os.environ["OLLAMA_ACCELERATOR"] = "metal"
        embeddings = OllamaEmbeddings(model="llama3")
    elif text == 'all-mpnet-base-v2':
        import os
        
        os.environ["TOKENIZERS_PARALLELISM"] = "false"  # Prevent tokenizer from using multiprocessing
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")

        return embeddings

