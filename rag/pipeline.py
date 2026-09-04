"""
RAG Pipeline — Documents ko embed karke FAISS mein store karta hai
Phir agents ke liye relevant chunks dhundhta hai

EMBEDDING MODEL: HuggingFace all-MiniLM-L6-v2 (FREE, runs locally)
- No API key needed for embeddings
- ~22MB model, downloads once on first run
- Works perfectly for our small 7-document knowledge base
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS

load_dotenv()

# Try HuggingFace embeddings first (FREE), fallback to Qwen if available
try:
    from langchain_huggingface import HuggingFaceEmbeddings
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
    print("[RAG] Using FREE HuggingFace embeddings (all-MiniLM-L6-v2)")
except ImportError:
    # Fallback: try Qwen embeddings (needs paid API)
    from langchain_openai import OpenAIEmbeddings
    embeddings = OpenAIEmbeddings(
        model=os.getenv("QWEN_EMBED_MODEL", "text-embedding-v3"),
        openai_api_key=os.getenv("DASHSCOPE_API_KEY"),
        openai_api_base=os.getenv("QWEN_BASE_URL"),
    )
    print("[RAG] Using Qwen embeddings (API-based)")

# Global variable — yeh poore app mein use hoga
vector_store = None


def build_vector_store():
    """
    Startup pe ek baar call hoga.
    RAG documents load -> chunk -> embed -> FAISS store banao
    """
    global vector_store

    knowledge_base_path = Path(__file__).parent / "knowledge_base"

    # Step A: Saare .md files load karo
    loader = DirectoryLoader(
        str(knowledge_base_path),
        glob="**/*.md",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
    )
    documents = loader.load()
    print(f"[RAG] Loaded {len(documents)} documents from knowledge base")

    # Step B: Chhote chunks mein todo (500 characters, 50 overlap)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n## ", "\n### ", "\n\n", "\n", ". ", " "],
    )
    chunks = splitter.split_documents(documents)
    print(f"[RAG] Split into {len(chunks)} chunks")

    # Step C: Embed karo aur FAISS mein store karo
    vector_store = FAISS.from_documents(chunks, embeddings)
    print(f"[RAG] FAISS vector store built with {len(chunks)} vectors")

    return vector_store


def search_knowledge(query: str, k: int = 5) -> str:
    """
    Agent yeh call karega jab usse context chahiye.
    Returns: relevant chunks as a single string
    """
    if vector_store is None:
        build_vector_store()

    results = vector_store.similarity_search(query, k=k)

    # Saare chunks ko ek string mein combine karo
    context = "\n\n---\n\n".join([
        f"[Source: {doc.metadata.get('source', 'unknown')}]\n{doc.page_content}"
        for doc in results
    ])
    return context