# KnowledgePilot AI backend

FastAPI backend for user accounts, PDF ingestion, document-grounded chat, citations, and conversation history.

## Setup

From the repository root in PowerShell:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Set server-side configuration in the root `.env` or in `backend\.env`. At minimum, configure `GROQ_API_KEY` to use the Groq answer provider. The backend reads `DATABASE_URL`, `GROQ_MODEL`, `EMBEDDING_MODEL`, `UPLOAD_DIR`, `JWT_SECRET_KEY`, `MAX_UPLOAD_SIZE_BYTES`, and `CORS_ORIGINS` from the environment. If no database URL is supplied, development uses a local SQLite database. For PostgreSQL, use a database with pgvector available; the service creates the `vector` extension on startup. The configured embedding model must return 384-dimensional vectors.

The PostgreSQL schema is in `app/db/init_db.sql`. To initialize it manually, connect to the target database and run `psql "$env:DATABASE_URL" -f app/db/init_db.sql` from PowerShell while in `backend`. The SQL is idempotent and creates the tables and indexes used by the API; application startup also creates any missing ORM tables and enables pgvector.

The embedding model is loaded on first upload or chat request and may download its model files on first use. Upload processing is synchronous; only text-based PDFs are supported (scanned PDFs need OCR).

## Run the API

From `backend` with the virtual environment active:

```powershell
uvicorn app.main:app --reload
```

Set configuration in the PowerShell environment before starting the server, or create a `backend\.env` file and run `uvicorn app.main:app --reload --env-file .env` from the backend directory. You can also use `--env-file ..\.env` to load the repository-root `.env` file.

The health endpoint is `http://127.0.0.1:8000/health`; interactive API documentation is at `http://127.0.0.1:8000/docs`.

## Automated tests

Tests use SQLite and fake embedding/Groq services, so they do not need PostgreSQL, a Groq key, or a downloaded model:

The answer client uses Groq's OpenAI-compatible API at `https://api.groq.com/openai/v1`. Configure `GROQ_API_KEY` and a model available to your Groq account with `GROQ_MODEL`. The default model is `llama-3.3-70b-versatile`.

```powershell
python -m unittest discover -s tests -v
```

## Manual API walkthrough

Use the Swagger UI at `/docs`, or run these PowerShell commands while the server is running:

```powershell
$base = "http://127.0.0.1:8000"
$account = @{ email = "you@example.com"; password = "a-long-local-test-password" } | ConvertTo-Json
$registered = Invoke-RestMethod -Method Post -Uri "$base/api/v1/auth/register" -ContentType "application/json" -Body $account
$login = Invoke-RestMethod -Method Post -Uri "$base/api/v1/auth/login" -ContentType "application/json" -Body $account
$headers = @{ Authorization = "Bearer $($login.access_token)" }
```

Create a small text PDF on your machine, then upload it:

```powershell
$pdf = "C:\path\to\sample.pdf"
$document = curl.exe -sS -X POST "$base/api/v1/documents" -H "Authorization: Bearer $($login.access_token)" -F "file=@$pdf" | ConvertFrom-Json
$document
Invoke-RestMethod -Method Get -Uri "$base/api/v1/documents" -Headers $headers
```

Ask a question against that document. Citations are generated from retrieved chunks, not from model-provided page or document identifiers:

```powershell
$chat = @{
    question = "What does this document say?"
    document_ids = @($document.id)
} | ConvertTo-Json
$answer = Invoke-RestMethod -Method Post -Uri "$base/api/v1/chat" -Headers $headers -ContentType "application/json" -Body $chat
$answer
Invoke-RestMethod -Method Get -Uri "$base/api/v1/conversations/$($answer.conversation_id)/messages" -Headers $headers
```

Finally, delete the uploaded document when done:

```powershell
Invoke-RestMethod -Method Delete -Uri "$base/api/v1/documents/$($document.id)" -Headers $headers
```

To confirm authorization, register a second account and try that account's token against the first account's document ID; the API should return `404`. Questions without relevant passages return an explicit uncertainty answer with an empty citation list. Groq-backed answers require a valid `GROQ_API_KEY` and network access.

## API endpoints

- `POST /api/v1/auth/register`, `POST /api/v1/auth/login`, `GET /api/v1/auth/me`
- `POST /api/v1/documents`, `GET /api/v1/documents`, `GET /api/v1/documents/{id}`, `DELETE /api/v1/documents/{id}`
- `POST /api/v1/chat`
- `GET /api/v1/conversations`, `GET /api/v1/conversations/{id}/messages`
- `GET /health`
