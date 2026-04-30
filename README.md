# FastAPI RAG Bot (Backend + Next.js Frontend)

Production-ready full-stack structure with:
- `backend`: FastAPI RAG API
- `frontend`: Next.js 14 (App Router) + Tailwind chat UI

## Folder Structure

```text
fastapi_bot/
  backend/
    __init__.py
    main.py
    rag_core.py
    requirements.txt
    chroma_db/
  frontend/
    app/
      globals.css
      layout.js
      page.js
    components/
      ChatBox.js
      FileUpload.js
    package.json
    package-lock.json
    tailwind.config.js
    postcss.config.js
    next.config.js
    .eslintrc.json
  .env
  .gitignore
  GUIDELINES.md
  README.md
```

## Backend Setup (FastAPI)

1. Create/activate Python virtual environment.
2. Install dependencies:

```bash
pip install -r backend/requirements.txt
```

3. Add environment variable in `.env` (root):

```env
GROQ_API_KEY=your_groq_key_here
```

4. Start backend from project root:

```bash
uvicorn backend.main:app --reload
```

Backend URL: `http://127.0.0.1:8000`

## Frontend Setup (Next.js 14)

1. Install frontend dependencies:

```bash
cd frontend
npm install
```

2. Start frontend:

```bash
npm run dev
```

Frontend URL: `http://localhost:3000`

## API Endpoints

- `POST /upload`
  - `multipart/form-data`
  - field: `file`
- `POST /ask`
  - body: `{ "query": "string" }`
  - returns: `{ "answer": "string" }`
- `DELETE /reset`
- `GET /health`

## Frontend Features

- Drag-and-drop file upload + file picker
- ChatGPT-style chat UI
- Chat memory stored in state
- Reset button to clear backend memory + UI
- API integration with `axios` (`http://127.0.0.1:8000`)
- Responsive clean design with rounded cards and soft shadows
- Error handling for failed API calls
