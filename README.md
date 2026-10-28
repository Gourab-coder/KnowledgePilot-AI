# KnowledgePilot AI

A document-grounded assistant with a React + Vite frontend and FastAPI backend. Upload text-based PDFs, ask questions about selected documents, and view answers with page citations.

## Run locally on Windows

You need Python 3.10+ and Node.js 20.19+ (or 22.12+). The frontend talks to the API through the Vite development proxy, so run both servers locally.

### 1. Configure and start the backend

Open PowerShell in the repository root:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
```

If `backend\.venv` does not exist yet, create it and install the backend dependencies first:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Create `backend\.env` with your Groq key and local development settings. This file is ignored by Git:

```dotenv
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.3-70b-versatile
DATABASE_URL=sqlite:///./knowledgepilot.db
JWT_SECRET_KEY=replace_with_a_long_random_secret
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
UPLOAD_DIR=./uploads
```

Generate a signing secret in PowerShell instead of using the example value:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Copy the printed value into `JWT_SECRET_KEY`, then start the API:

```powershell
uvicorn app.main:app --reload --env-file .env
```

On first PDF upload, the embedding model downloads if it is not already cached. A working `GROQ_API_KEY` and internet connection are required for Groq-generated answers. The backend creates its local SQLite database automatically.

### 2. Start the frontend

Open a second PowerShell window at the repository root:

```powershell
cd frontend
npm install
npm run dev
```

Open the Vite URL printed in the terminal (by default, `http://127.0.0.1:5173`). Keep both terminals running. The development server forwards `/api` requests to `http://127.0.0.1:8000`.

### 3. Try the app

1. Register an account or sign in.
2. Add a text-based PDF using **Add a PDF** or drag one into the chat area.
3. Select the documents to search in the sidebar.
4. Ask a question; inspect the answer's source excerpts and page numbers.
5. Open a previous conversation or delete a document from your library.

Scanned/image-only PDFs need OCR and are not supported yet. For API troubleshooting, open `http://127.0.0.1:8000/docs`. To run backend tests, from the `backend` directory use `python -m unittest discover -s tests -v`.

## Production build

From `frontend`, run `npm run build`. The generated static frontend is written to `frontend/dist`. Configure the production API URL with `VITE_API_BASE_URL` at build time and set the backend's production secrets, database, and CORS origins separately. Do not put the Groq API key in frontend configuration.