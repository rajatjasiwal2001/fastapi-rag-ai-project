import os
import re
from pathlib import Path
from typing import List

import chromadb
from groq import Groq
from sentence_transformers import SentenceTransformer


# ----------------------------
# CHUNKING
# ----------------------------
def chunk_text(text: str, chunk_size: int = 400, overlap: int = 50) -> List[str]:
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

print("Loading embedding model...")
embedder = SentenceTransformer("all-MiniLM-L6-v2")

client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = client.get_or_create_collection(name=COLLECTION_NAME)


def build_vector_store(chunks: List[str]):
    if len(collection.get().get("ids", [])) > 0:
        print("Using existing vector DB (skip rebuild)")
        return

    print("Building vector store...")

    ids = [f"chunk-{i}" for i in range(len(chunks))]
    embeddings = embedder.encode(chunks).tolist()

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
def retrieve_context(query: str, top_k: int = 3) -> str:
    query_embedding = embedder.encode([query]).tolist()[0]

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