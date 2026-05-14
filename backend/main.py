from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from io import BytesIO
from pypdf import PdfReader

from .rag_core import index_text, retrieve_context, ask_groq, collection

load_dotenv()

app = FastAPI(title="GenAI RAG API 🚀")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

chat_history = []

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    answer: str

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        content = await file.read()
        text = ""

        filename = file.filename.lower()
        if filename.endswith(".txt"):
            text = content.decode("utf-8")

        elif filename.endswith(".pdf"):
            pdf = PdfReader(BytesIO(content))
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
        else:
            raise HTTPException(status_code=400, detail="Only .txt and .pdf supported")

        if not text.strip():
            raise HTTPException(status_code=400, detail="No readable text found")

        index_text(text)

        return {"message": f"{file.filename} indexed successfully"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/ask", response_model=QueryResponse)
def ask_question(payload: QueryRequest):
    try:
        context = retrieve_context(payload.query, top_k=8)

        final_query = f"""
Question:
{payload.query}
"""

        answer = ask_groq(final_query, context)

        chat_history.append(f"Q: {payload.query}")
        chat_history.append(f"A: {answer}")

        return {"answer": answer}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/reset")
def reset():
    ids = collection.get().get("ids", [])
    if ids:
        collection.delete(ids=ids)

    chat_history.clear()
    return {"message": "Reset successful"}