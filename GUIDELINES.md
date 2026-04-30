# Project Guidelines

## 1) Architecture

- Keep backend code inside `backend/`.
- Keep frontend code inside `frontend/`.
- Do not mix Python API files with Next.js files at root.

## 2) Backend Standards

- Main API entrypoint: `backend/main.py`.
- RAG/core logic: `backend/rag_core.py`.
- Keep API routes thin; keep business logic in helper/core modules.
- Add new dependencies in `backend/requirements.txt`.
- For file upload endpoints, keep `python-multipart` installed.

## 3) Frontend Standards

- Use Next.js App Router conventions (`frontend/app`).
- Use reusable UI in `frontend/components`.
- Keep API base URL centralized in components or shared config.
- Use `axios` for API requests.
- Always show user-friendly error states.

## 4) UI/UX Standards

- Maintain minimal clean interface.
- Use rounded cards and soft shadows.
- Ensure mobile + desktop responsiveness.
- Keep chat layout consistent:
  - User messages on right
  - AI messages on left

## 5) State & Data Handling

- Chat memory should remain in React state.
- Clear state on reset success.
- Handle loading states for upload and ask flows.

## 6) Reliability

- Validate and sanitize user input.
- Return meaningful backend HTTP errors.
- Surface backend errors in frontend UI.

## 7) Run Commands

From root:

- Backend:
  - `uvicorn backend.main:app --reload`
- Frontend:
  - `cd frontend`
  - `npm run dev`

## 8) Future Improvements

- Add frontend environment file for API base URL (`NEXT_PUBLIC_API_BASE_URL`).
- Add unit/integration tests for backend routes.
- Add frontend component tests.
- Restrict CORS origins for production deployment.
