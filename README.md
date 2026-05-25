# TaskMind AI

AI assisted task management app with FastAPI, PostgreSQL + pgvector, Streamlit, and planning support from LLM workflows.

## Architecture

```text
TaskMind AI
├─ web        Streamlit frontend
├─ api        FastAPI backend
└─ postgres   PostgreSQL with pgvector
```

For production, deploy all three services inside one Railway project:

- `web` is public and serves the Streamlit UI.
- `api` can stay private and is called by `web` over Railway private networking.
- `postgres` is attached to the API service through `DATABASE_URL`.

## Local Development

Create a local env file:

```bash
cp .env.example .env
```

Run the full stack with Docker:

```bash
docker compose up --build
```

Open:

- Streamlit web: http://localhost:8501
- FastAPI docs: http://localhost:8000/docs

## Railway Deployment

Create one Railway project with these services.

### 1. Database

Add a PostgreSQL service with pgvector support. Set the API service `DATABASE_URL` to the database connection URL Railway provides.

### 2. API Service

Create a service from this repository and configure:

```text
Dockerfile path: Dockerfile.api
Public domain: optional
```

Required variables:

```env
PORT=8000
DATABASE_URL=${{Postgres.DATABASE_URL}}
SECRET_KEY=replace-with-a-long-random-secret
GROQ_API_KEY=your-groq-key
OPENAI_API_KEY=optional
TELEGRAM_TOKEN=optional
CHAT_ID=optional
```

Set `PORT=8000` on the API service so the Streamlit service can call a stable private address.

### 3. Web Service

Create another service from the same repository and configure:

```text
Dockerfile path: Dockerfile.web
Public domain: enabled
```

Set the frontend API URL to the internal Railway service address:

```env
TASKMIND_API_URL=http://api.railway.internal:8000
```

If your Railway API service has a different service name, replace `api` with that name.

## Key Features

- JWT authentication
- Task creation with due dates and priorities
- Calendar view
- AI question answering over tasks
- Tomorrow plan generation
- Telegram reminder scheduler

## Important Notes

- Keep frontend and backend in the same Railway project/environment to use private networking.
- Use the Streamlit service as the public entry point.
- Avoid committing `.env` or real credentials.
- Use a strong `SECRET_KEY` in production.
