# app/ingest.py
import os
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import (
    TextLoader,
    PDFPlumberLoader,
    CSVLoader,
    UnstructuredHTMLLoader,
    UnstructuredWordDocumentLoader,
)
from langchain_unstructured import UnstructuredLoader  # NEW loader for fallback
from app import config

def load_documents():
    docs = []
    for file in os.listdir(config.DOCUMENT_PATH):
        path = os.path.join(config.DOCUMENT_PATH, file)
        fname = file.lower()
        # Explicitly use best loader per file type
        if file.endswith(".txt"):
            loader = TextLoader(path)
        elif file.endswith(".pdf"):
            loader = PDFPlumberLoader(path)
        elif file.endswith(".csv"):
            loader = CSVLoader(path)
        elif file.endswith(".html") or file.endswith(".htm"):
            loader = UnstructuredHTMLLoader(path)
        elif file.endswith(".docx") or file.endswith(".doc"):
            loader = UnstructuredWordDocumentLoader(path)
        else:
            loader = UnstructuredLoader(path)  # Fallback, non-deprecated
        try:
            loaded_docs = loader.load()
        except Exception as e:
            print(f"⚠️ Could not load {file}: {e}")
            continue
        # Assign categories based on filename keywords
        if "broadcast" in fname:
            doc_cat = "broadcast"
        elif "crm" in fname:
            doc_cat = "crm"
        elif "chat" in fname or "chatbot" in fname:
            doc_cat = "chat"
        elif "marketing-template" in fname or "ads-" in fname or "ads" in fname:
            doc_cat = "marketing"
        elif "task" in fname or "tasks" in fname or "task-management" in fname:
            doc_cat = "task_management"
        elif "team-member" in fname or "team-management" in fname:
            doc_cat = "team_management"
        elif "how-to-add" in fname or "how-to-assign" in fname or "how-to-delete" in fname or "how-to-update" in fname:
            doc_cat = "how_to"
        elif "import-contacts" in fname or "xport-contacts" in fname or "contacts" in fname:
            doc_cat = "contacts"
        elif "automatic-" in fname or "auto-" in fname:
            doc_cat = "automation"
        elif "live-agent" in fname:
            doc_cat = "live_agent"
        elif "qr-code" in fname:
            doc_cat = "qr_code"
        elif "default-fallback" in fname:
            doc_cat = "fallback"
        else:
            doc_cat = "general"
        for doc in loaded_docs:
            doc.metadata["category"] = doc_cat
        docs.extend(loaded_docs)
    return docs

def split_documents(documents):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP
    )
    return splitter.split_documents(documents)

def embed_and_store(docs):
    embeddings = HuggingFaceEmbeddings(model_name=config.EMBEDDING_MODEL_PATH)
    vectorstore = FAISS.from_documents(docs, embeddings)
    vectorstore.save_local(config.VECTORSTORE_PATH)
    print(f"✅ Vectorstore saved at: {config.VECTORSTORE_PATH}")

def run_ingest():
    print("📄 Loading documents...")
    raw_docs = load_documents()
    print("🧩 Splitting documents...")
    chunks = split_documents(raw_docs)
    print("🔗 Embedding & storing vectorstore...")
    embed_and_store(chunks)

if __name__ == "__main__":
    run_ingest()
