# app/config.py

VECTORSTORE_PATH = "vectorstore/faiss_index"
DOCUMENT_PATH = "data/docs"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100

# Use local path to saved embedding model
EMBEDDING_MODEL_PATH = "models/bge-small-en"

# Local LLM details (Ollama or LM Studio)
LLM_MODEL = "llama2-uncensored:7b"
LLM_BASE_URL = "http://localhost:11434"
