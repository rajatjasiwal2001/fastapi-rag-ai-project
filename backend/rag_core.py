import os
import re
from pathlib import Path
from typing import List
import math

import chromadb
from groq import Groq


# ----------------------------
# CHUNKING
# ----------------------------
def chunk_text(text: str, chunk_size: int = 250, overlap: int = 50) -> List[str]:
    sentences = re.split(r'(?<=[.!?]) +', text)

    chunks = []
    current_chunk = []
    current_length = 0

    for sentence in sentences:
        words = sentence.split()

        if current_length + len(words) > chunk_size:
            chunks.append(" ".join(current_chunk))

            current_chunk = current_chunk[-overlap:] if overlap < len(current_chunk) else current_chunk
            current_length = len(current_chunk)

        current_chunk.extend(words)
        current_length += len(words)

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


# ----------------------------
# VECTOR STORE (LOAD ONCE)
# ----------------------------
CHROMA_PATH = str(Path(__file__).resolve().parent / "chroma_db")
COLLECTION_NAME = "documents"

EMBED_DIM = 384


def _lightweight_embed(text: str, dim: int = EMBED_DIM) -> List[float]:
    """
    Deterministic fallback embedding used when sentence-transformers is unavailable.
    It keeps the API running in constrained Python environments.
    """
    vec = [0.0] * dim
    tokens = re.findall(r"\w+", text.lower())
    if not tokens:
        return vec

    for token in tokens:
        idx = hash(token) % dim
        vec[idx] += 1.0

    norm = math.sqrt(sum(v * v for v in vec))
    if norm > 0:
        vec = [v / norm for v in vec]

    return vec


class FallbackEmbedder:
    def encode(self, texts):
        return [_lightweight_embed(text) for text in texts]


def _build_embedder():
    try:
        from sentence_transformers import SentenceTransformer

        print("Loading embedding model: all-MiniLM-L6-v2")
        return SentenceTransformer("all-MiniLM-L6-v2")
    except Exception as exc:
        print(f"Warning: sentence-transformers unavailable ({exc}). Using fallback embedder.")
        return FallbackEmbedder()


def _as_list(vectors):
    return vectors.tolist() if hasattr(vectors, "tolist") else vectors


embedder = _build_embedder()

client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = client.get_or_create_collection(name=COLLECTION_NAME)


def build_vector_store(chunks: List[str]):
    if len(collection.get().get("ids", [])) > 0:
        print("Using existing vector DB (skip rebuild)")
        return

    print("Building vector store...")

    ids = [f"chunk-{i}" for i in range(len(chunks))]
    embeddings = _as_list(embedder.encode(chunks))

    collection.add(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
    )

    print("Vector store ready")


# ----------------------------
# INDEX TEXT (for upload API)
# ----------------------------
def index_text(text: str):
    chunks = chunk_text(text)
    build_vector_store(chunks)


# ----------------------------
# RETRIEVE
# ----------------------------
def retrieve_context(query: str, top_k: int = 2) -> str:
    query_embedding = _as_list(embedder.encode([query]))[0]

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
    )

    docs = results.get("documents", [[]])[0]
    return "\n\n".join(docs)


# ----------------------------
# LLM (CONTROLLED OUTPUT)
# ----------------------------
def ask_groq(query: str, context: str) -> str:
    api_key = os.getenv("GROQ_API_KEY", "").strip()

    if not api_key:
        raise ValueError("Missing GROQ_API_KEY in .env")

    client = Groq(api_key=api_key)

    prompt = f"""
Answer using ONLY the given context.

Rules:
- Max 5 lines
- Be concise
- No repetition
- If not found, say "I don't know"

Context:
{context}

Question:
{query}
"""

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=200,
    )

    return completion.choices[0].message.content.strip()