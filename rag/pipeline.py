# """
# RAG Pipeline — Documents ko embed karke FAISS mein store karta hai
# Phir agents ke liye relevant chunks dhundhta hai

# EMBEDDING MODEL: HuggingFace all-MiniLM-L6-v2 (FREE, runs locally)
# - No API key needed for embeddings
# - ~22MB model, downloads once on first run
# - Works perfectly for our small 7-document knowledge base
# """
# import os
# from pathlib import Path
# from dotenv import load_dotenv
# from langchain_community.document_loaders import DirectoryLoader, TextLoader
# from langchain_text_splitters import RecursiveCharacterTextSplitter
# from langchain_community.vectorstores import FAISS

# load_dotenv()

# # Try HuggingFace embeddings first (FREE), fallback to Qwen if available
# try:
#     from langchain_huggingface import HuggingFaceEmbeddings
#     embeddings = HuggingFaceEmbeddings(
#         model_name="sentence-transformers/all-MiniLM-L6-v2",
#         model_kwargs={"device": "cpu"},
#         encode_kwargs={"normalize_embeddings": True},
#     )
#     print("[RAG] Using FREE HuggingFace embeddings (all-MiniLM-L6-v2)")
# except ImportError:
#     # Fallback: try Qwen embeddings (needs paid API)
#     from langchain_openai import OpenAIEmbeddings
#     embeddings = OpenAIEmbeddings(
#         model=os.getenv("QWEN_EMBED_MODEL", "text-embedding-v3"),
#         openai_api_key=os.getenv("DASHSCOPE_API_KEY"),
#         openai_api_base=os.getenv("QWEN_BASE_URL"),
#     )
#     print("[RAG] Using Qwen embeddings (API-based)")

# # Global variable — yeh poore app mein use hoga
# vector_store = None


# def build_vector_store():
#     """
#     Startup pe ek baar call hoga.
#     RAG documents load -> chunk -> embed -> FAISS store banao
#     """
#     global vector_store

#     knowledge_base_path = Path(__file__).parent / "knowledge_base"

#     # Step A: Saare .md files load karo
#     loader = DirectoryLoader(
#         str(knowledge_base_path),
#         glob="**/*.md",
#         loader_cls=TextLoader,
#         loader_kwargs={"encoding": "utf-8"},
#     )
#     documents = loader.load()
#     print(f"[RAG] Loaded {len(documents)} documents from knowledge base")

#     # Step B: Chhote chunks mein todo (500 characters, 50 overlap)
#     splitter = RecursiveCharacterTextSplitter(
#         chunk_size=500,
#         chunk_overlap=50,
#         separators=["\n## ", "\n### ", "\n\n", "\n", ". ", " "],
#     )
#     chunks = splitter.split_documents(documents)
#     print(f"[RAG] Split into {len(chunks)} chunks")

#     # Step C: Embed karo aur FAISS mein store karo
#     vector_store = FAISS.from_documents(chunks, embeddings)
#     print(f"[RAG] FAISS vector store built with {len(chunks)} vectors")

#     return vector_store


# def search_knowledge(query: str, k: int = 5) -> str:
#     """
#     Agent yeh call karega jab usse context chahiye.
#     Returns: relevant chunks as a single string
#     """
#     if vector_store is None:
#         build_vector_store()

#     results = vector_store.similarity_search(query, k=k)

#     # Saare chunks ko ek string mein combine karo
#     context = "\n\n---\n\n".join([
#         f"[Source: {doc.metadata.get('source', 'unknown')}]\n{doc.page_content}"
#         for doc in results
#     ])
#     return context

"""
RAG Pipeline — Documents ko embed karke in-memory vector store mein rakhta hai
Phir agents ke liye relevant chunks dhundhta hai

EMBEDDING STRATEGY (memory-optimized for 512MB Render free tier):
- Primary: fastembed (ONNX runtime, no torch needed, much lighter RAM)
  Local hai, koi per-request API cost/rate-limit nahi (HF se sirf ek baar
  model file download hota hai startup pe, jaisa kisi bhi ML model ka hota hai)
- Fallback: TF-IDF (scikit-learn) agar fastembed kisi wajah se load na ho
  sake (e.g. model download fail, network issue) — koi crash nahi, app
  degrade ho ke keyword-based search pe chali jaati hai

PEHLE: torch + sentence-transformers use hote thay (~600MB+ RAM sirf import
pe) — yeh Render free tier (512MB limit) pe OOM crash ka sabse bada
reason thay. Ab dono options milke bohot kam RAM use karte hain.
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import numpy as np

load_dotenv()

# ─── Global state ───
_chunks = None          # list of langchain Document chunks
_chunk_texts = None     # list[str] — same order as _chunks
_mode = None            # "fastembed" or "tfidf" — jo bhi load hua

# fastembed-specific globals
_fe_model = None
_chunk_embeddings = None  # np.ndarray, shape (n_chunks, dim)

# TF-IDF-specific globals
_vectorizer = None
_tfidf_matrix = None


def _load_and_chunk_documents():
    """Knowledge base ke saare .md files load karo aur chunk karo"""
    knowledge_base_path = Path(__file__).parent / "knowledge_base"

    loader = DirectoryLoader(
        str(knowledge_base_path),
        glob="**/*.md",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
    )
    documents = loader.load()
    print(f"[RAG] Loaded {len(documents)} documents from knowledge base")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n## ", "\n### ", "\n\n", "\n", ". ", " "],
    )
    chunks = splitter.split_documents(documents)
    print(f"[RAG] Split into {len(chunks)} chunks")
    return chunks


def build_vector_store():
    """
    Startup pe (ya pehli search_knowledge() call pe) ek baar chalega.
    Pehle fastembed try karta hai (behtar semantic search), agar wo fail
    ho to TF-IDF pe fallback kar leta hai — dono case mein app chalta rehta
    hai, crash nahi hota.
    """
    global _chunks, _chunk_texts, _mode, _fe_model, _chunk_embeddings
    global _vectorizer, _tfidf_matrix

    _chunks = _load_and_chunk_documents()
    _chunk_texts = [c.page_content for c in _chunks]

    # ── Try fastembed first (local ONNX, no torch, no per-request API cost) ──
    try:
        from fastembed import TextEmbedding

        _fe_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
        embeddings = list(_fe_model.embed(_chunk_texts))
        _chunk_embeddings = np.array(embeddings)
        _mode = "fastembed"
        print(f"[RAG] Using fastembed (BAAI/bge-small-en-v1.5) — "
              f"{len(_chunk_texts)} chunks embedded")

    except Exception as e:
        # Fastembed load fail hua (model download issue, etc.) —
        # TF-IDF pe fallback karo, app crash nahi hoga
        print(f"[RAG] fastembed unavailable ({e}), falling back to TF-IDF")
        from sklearn.feature_extraction.text import TfidfVectorizer

        _vectorizer = TfidfVectorizer(stop_words="english")
        _tfidf_matrix = _vectorizer.fit_transform(_chunk_texts)
        _mode = "tfidf"
        print(f"[RAG] Using TF-IDF — {len(_chunk_texts)} chunks indexed")

    return _mode


def search_knowledge(query: str, k: int = 5) -> str:
    """
    Agent yeh call karega jab usse context chahiye.
    Returns: relevant chunks as a single string (same format as pehle)
    """
    if _mode is None:
        build_vector_store()

    if _mode == "fastembed":
        q_embedding = list(_fe_model.embed([query]))[0]
        sims = np.dot(_chunk_embeddings, q_embedding) / (
            np.linalg.norm(_chunk_embeddings, axis=1) * np.linalg.norm(q_embedding)
            + 1e-10
        )
        top_idx = sims.argsort()[::-1][:k]
    else:  # tfidf
        from sklearn.metrics.pairwise import cosine_similarity

        q_vec = _vectorizer.transform([query])
        sims = cosine_similarity(q_vec, _tfidf_matrix)[0]
        top_idx = sims.argsort()[::-1][:k]

    results = [_chunks[i] for i in top_idx]

    context = "\n\n---\n\n".join([
        f"[Source: {doc.metadata.get('source', 'unknown')}]\n{doc.page_content}"
        for doc in results
    ])
    return context
