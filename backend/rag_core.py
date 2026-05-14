import os
import re
import uuid
import math
from pathlib import Path
from typing import List

import chromadb
from groq import Groq


# ----------------------------
# CHUNKING
# ----------------------------
# Split text into overlapping chunks so the retriever can match questions even
# when the answer appears across sentence boundaries.
# ----------------------------

def chunk_text(text: str, chunk_size: int = 200, overlap: int = 75) -> List[str]:
    normalized = re.sub(r"\s+", " ", text.replace("\n", " ")).strip()
    if not normalized:
        return []

    words = normalized.split(" ")
    chunks = []
    start = 0

    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunks.append(" ".join(words[start:end]))

        if end == len(words):
            break

        start = max(end - overlap, end)

    return chunks


# ----------------------------
# VECTOR STORE (LOAD ONCE)
# ----------------------------
CHROMA_PATH = str(Path(__file__).resolve().parent / "chroma_db")
COLLECTION_NAME = "documents"
EMBED_DIM = 384


def _lightweight_embed(text: str, dim: int = EMBED_DIM) -> List[float]:
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


def add_chunks_to_vector_store(chunks: List[str]):
    if not chunks:
        return

    ids = [str(uuid.uuid4()) for _ in chunks]
    embeddings = _as_list(embedder.encode(chunks))

    collection.add(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
    )

    if hasattr(client, "persist"):
        client.persist()

    print(f"Indexed {len(chunks)} chunk(s) into ChromaDB")


# ----------------------------
# INDEX TEXT (for upload API)
# ----------------------------
def index_text(text: str):
    chunks = chunk_text(text)
    add_chunks_to_vector_store(chunks)


# ----------------------------
# RETRIEVE
# ----------------------------
def retrieve_context(query: str, top_k: int = 8) -> str:
    query_embedding = _as_list(embedder.encode([query]))[0]

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "distances"],
    )

    docs = results.get("documents", [[]])[0]
    if not docs:
        return ""

    return "\n\n---\n\n".join(doc for doc in docs if doc)


# ----------------------------
# LLM (CONTROLLED OUTPUT)
# ----------------------------
def ask_groq(query: str, context: str) -> str:
    api_key = os.getenv("GROQ_API_KEY", "").strip()

    if not api_key:
        raise ValueError("Missing GROQ_API_KEY in .env")

    if not context.strip():
        return "I don't know"

    client = Groq(api_key=api_key)
    prompt = f"""
Answer using ONLY the given context.

Rules:
- Answer directly with the information from the context.
- Do not invent or hallucinate.
- If the answer is not found in the context, say "I don't know".

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