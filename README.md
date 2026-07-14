# Ali Raza's Assistant

A production-style full-stack chatbot built from basic_chatbot.ipynb.

- React and TypeScript frontend
- FastAPI and LangGraph backend
- Groq-hosted openai/gpt-oss-120b
- PostgreSQL with Tortoise ORM
- Aerich database migrations
- Docker Compose for frontend, API, migrations, and PostgreSQL
- Token-by-token Server-Sent Events streaming

Read [BUILD_GUIDE.md](BUILD_GUIDE.md) for the architecture and development
workflow.

For production deployment with Vercel, Railway, and managed PostgreSQL, read
[DEPLOYMENT.md](DEPLOYMENT.md).

## Features

- Persistent conversations and messages
- Create, search, rename, and delete conversations
- Stop generation, regenerate the latest answer, and copy responses
- Markdown, tables, links, and fenced code blocks
- Dark, light, and system themes
- Responsive desktop and mobile interface
- Database health reporting
- Backend lifecycle tests and frontend build tests

## Project structure

    ali-raza-assistant/
    ├── backend/
    │   ├── app/
    │   │   ├── api/
    │   │   ├── core/
    │   │   ├── models/
    │   │   ├── repositories/
    │   │   └── services/
    │   ├── migrations/
    │   ├── tests/
    │   ├── Dockerfile
    │   └── pyproject.toml
    ├── frontend/
    │   ├── app/
    │   ├── Dockerfile
    │   └── package.json
    ├── compose.yaml
    └── .env.example

## Recommended setup: Docker

Install Docker Desktop, then create the root environment file:

    Copy-Item .env.example .env
    notepad .env

Replace your_groq_api_key_here and change POSTGRES_PASSWORD when the stack is
used outside local development.

If ports 5432, 8000, or 3000 are already in use, change POSTGRES_PORT,
BACKEND_PORT, FRONTEND_PORT, and NEXT_PUBLIC_API_URL in .env before building.

Build and start everything:

    docker compose up --build

Docker Compose starts PostgreSQL, waits for it to become healthy, applies
Aerich migrations, starts the API, and then starts the frontend.

Open:

- Frontend: http://localhost:3000
- API health: http://localhost:8000/api/health
- API documentation: http://localhost:8000/docs

Stop the stack:

    docker compose down

Stop it and delete the PostgreSQL volume:

    docker compose down -v

The second command permanently removes local container database data.

## Local development with Docker PostgreSQL

Start only PostgreSQL:

    docker compose up -d db

Create and activate the backend environment:

    cd backend
    python -m venv venv
    .\venv\Scripts\Activate.ps1
    python -m pip install -e ".[dev]"
    Copy-Item ..\.env.example .env

Add the Groq key to backend/.env, then apply migrations:

    python -m aerich upgrade

Start the API:

    python -m uvicorn app.main:app --reload --port 8000

In a second terminal:

    cd frontend
    Copy-Item .env.example .env.local
    npm install
    npm run dev

## Aerich migration workflow

Tortoise models live in backend/app/models/entities.py. After changing them:

    cd backend
    .\venv\Scripts\Activate.ps1
    python -m aerich migrate --name describe_your_change
    python -m aerich upgrade

Inspect migration state:

    python -m aerich history
    python -m aerich heads

Roll back the latest migration:

    python -m aerich downgrade

Review generated migration files before applying them, especially when Aerich
asks whether a field was renamed. Choosing a drop instead of a rename can lose
data.

## Verification

Backend:

    cd backend
    .\venv\Scripts\python.exe -m pytest --basetemp .test-tmp

Frontend:

    cd frontend
    npm run lint
    npm run build
    node --test tests/rendered-html.test.mjs

Docker:

    docker compose config
    docker compose build
    docker compose up

## Moving from the old SQLite version

The PostgreSQL migration creates a new empty database. Existing messages in
backend/data/assistant.db are not copied automatically. Keep the SQLite file
until its data has either been exported or is no longer needed.

## Security notes

- Never commit .env or expose GROQ_API_KEY in the frontend.
- Use a strong PostgreSQL password outside local development.
- Add authentication and conversation ownership before public deployment.
- Restrict CORS_ORIGINS to the production frontend domain.
- Add rate limiting, request-size limits, monitoring, and backups.
