# Build guide: RazaMind

This guide explains how the notebook evolved into a containerized application
with PostgreSQL, Tortoise ORM, and Aerich migrations.

## 1. Notebook responsibilities

The notebook established:

1. LangGraph message state.
2. A ChatGroq model.
3. A graph node that invokes the model.
4. Streamed response chunks.

The production project replaces terminal input, hard-coded thread IDs, and
in-memory state with a React client, HTTP API, and PostgreSQL records.

## 2. Runtime architecture

    Browser
      |
      | HTTP and Server-Sent Events
      v
    React frontend :3000
      |
      v
    FastAPI and LangGraph :8000
      |
      | async Tortoise ORM
      v
    PostgreSQL :5432

Aerich runs as a one-shot migration service before the API starts in Docker
Compose.

## 3. Configuration

Backend settings are in backend/app/core/config.py.

Important values:

| Variable | Purpose |
| --- | --- |
| GROQ_API_KEY | Private Groq credential |
| GROQ_MODEL | Model identifier |
| DATABASE_URL | Tortoise database connection URL |
| GENERATE_SCHEMAS | Test-only automatic schema creation |
| CORS_ORIGINS | Allowed browser origins |

Production and normal development must keep GENERATE_SCHEMAS false. Aerich
migrations, not application startup, own the database schema.

## 4. Tortoise models

Models live in backend/app/models/entities.py.

Conversation stores:

- UUID primary key
- title
- creation timestamp
- update timestamp

Message stores:

- UUID primary key
- conversation foreign key with cascade deletion
- user or assistant role
- content
- ordered position
- creation timestamp

The conversation and position pair is unique. Repository writes lock the
conversation row before calculating the next position, preventing two
concurrent messages from receiving the same order.

## 5. Async repository and routes

backend/app/repositories/conversations.py contains all database operations.
Every method is async.

The FastAPI routes await repository calls. Streaming stays asynchronous while
user messages, partial answers, completed answers, titles, and regenerated
answers are persisted.

The health endpoint executes SELECT 1. A successful HTTP response therefore
confirms both the API process and database connection.

## 6. Aerich

Aerich reads:

    app.core.database.TORTOISE_ORM

Its project configuration is stored in backend/pyproject.toml and migration
files are stored in backend/migrations.

For an existing project after a model change:

    cd backend
    python -m aerich migrate --name add_example_field
    python -m aerich upgrade

Useful commands:

    python -m aerich history
    python -m aerich heads
    python -m aerich downgrade

Always inspect generated migrations. Renames require particular care because a
drop-and-add migration can destroy the old column data.

## 7. Docker services

compose.yaml defines:

| Service | Responsibility |
| --- | --- |
| db | PostgreSQL with a named persistent volume |
| migrate | Applies pending Aerich migrations and exits |
| backend | FastAPI and LangGraph API |
| frontend | Production React server |

The database health check uses pg_isready. The migration service waits for a
healthy database. The API waits for migration success. The frontend waits for
the API health check.

## 8. Docker workflow

Prepare secrets:

    Copy-Item .env.example .env
    notepad .env

Build and start:

    docker compose up --build

Inspect:

    docker compose ps
    docker compose logs -f migrate
    docker compose logs -f backend

Stop:

    docker compose down

Delete all container database data only when intentionally resetting:

    docker compose down -v

## 9. Local workflow

Use Docker only for PostgreSQL:

    docker compose up -d db

Run migrations and the API locally:

    cd backend
    .\venv\Scripts\Activate.ps1
    python -m pip install -e ".[dev]"
    python -m aerich upgrade
    python -m uvicorn app.main:app --reload --port 8000

Run the React client in another terminal:

    cd frontend
    npm install
    npm run dev

## 10. Testing strategy

API lifecycle tests use an isolated SQLite database through the same Tortoise
models. Automatic schema generation is enabled only in test settings.

Run:

    cd backend
    .\venv\Scripts\python.exe -m pytest --basetemp .test-tmp

Frontend checks:

    cd frontend
    npm run lint
    npm run build
    node --test tests/rendered-html.test.mjs

Container checks:

    docker compose config
    docker compose build
    docker compose up

## 11. Production checklist

1. Use managed PostgreSQL with backups and encrypted connections.
2. Put secrets in the hosting platform, not in source files.
3. Run Aerich upgrade as a release step before starting new API instances.
4. Restrict CORS to the real frontend domain.
5. Add authentication and ownership columns.
6. Add rate limiting, quotas, request IDs, and structured logs.
7. Monitor database connections, response latency, token usage, and errors.
8. Test restore procedures instead of assuming backups work.

## 12. SQLite data

The earlier backend/data/assistant.db file is not automatically imported into
PostgreSQL. Keep it as a backup until its conversation history is no longer
needed or a separate one-time data import has been completed.
