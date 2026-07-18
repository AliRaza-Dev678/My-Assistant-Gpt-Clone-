# Ali Raza's Assistant

A full-stack, ChatGPT-style AI assistant built from `basic_chatbot.ipynb` and
expanded into a production-ready web application.

## Live application

- Frontend: [ali-raza-assistant-web.vercel.app](https://ali-raza-assistant-web.vercel.app)
- Backend health: [Railway API health](https://my-assistant-gpt-clone-production.up.railway.app/api/health)
- Interactive API docs: [Railway Swagger UI](https://my-assistant-gpt-clone-production.up.railway.app/docs)
- Source: [GitHub repository](https://github.com/AliRaza-Dev678/My-Assistant-Gpt-Clone-)

> Google sign-in is used only to label observability traces; it is not yet
> conversation authorization. Conversations are not isolated by user account,
> so do not enter private or sensitive information in the public deployment.

## What it includes

- ChatGPT-inspired responsive interface
- Token-by-token responses with Server-Sent Events (SSE)
- Persistent conversations and messages
- Create, search, rename, and delete chats
- Stop generation and regenerate the latest response
- Markdown, tables, links, and fenced code blocks
- Light, dark, and system themes
- PostgreSQL persistence through Tortoise ORM
- Aerich database migrations
- FastAPI health checks and OpenAPI documentation
- LangSmith traces grouped into one thread per conversation
- Optional verified Google identity and anonymous browser-device trace labels
- Docker Compose development environment
- Automated Vercel and Railway deployments from GitHub

## Technology stack

| Layer | Technology |
| --- | --- |
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS |
| Backend | FastAPI, Python 3.12, LangChain, LangGraph |
| AI provider | Groq |
| Model | `openai/gpt-oss-120b` |
| Observability | LangSmith traces and conversation threads |
| Optional identity | Google Identity Services |
| Database | PostgreSQL 18 |
| ORM and migrations | Tortoise ORM and Aerich |
| Local containers | Docker Compose |
| Production hosting | Vercel, Railway, and Railway PostgreSQL |

## Production architecture

```text
Browser
  |
  v
Vercel (Next.js frontend)
  |
  | HTTPS + SSE
  v
Railway (FastAPI backend)
  |          |              \
  v          v               v
PostgreSQL   Groq API        LangSmith
```

Vercel serves the frontend. The frontend calls the Railway API, which stores
conversation data in PostgreSQL and streams model output from Groq. When
enabled, LangSmith receives model traces; an optional Google ID token is
verified by the backend before its identity is added to trace metadata.

## Project structure

```text
ali-raza-assistant/
|-- backend/
|   |-- app/
|   |   |-- api/           # FastAPI routes
|   |   |-- core/          # Settings and database lifecycle
|   |   |-- models/        # Tortoise entities and API schemas
|   |   |-- repositories/  # Conversation persistence
|   |   `-- services/      # LangGraph and Groq assistant
|   |-- migrations/        # Aerich migrations
|   |-- tests/
|   |-- Dockerfile
|   |-- railway.json
|   `-- pyproject.toml
|-- frontend/
|   |-- app/
|   |-- public/
|   |-- tests/
|   |-- Dockerfile
|   |-- package.json
|   `-- vercel.json
|-- compose.yaml
|-- .env.example
|-- BUILD_GUIDE.md
`-- DEPLOYMENT.md
```

## Quick start with Docker

### Prerequisites

- Docker Desktop
- A [Groq API key](https://console.groq.com/keys)

Create the local environment file:

```powershell
Copy-Item .env.example .env
notepad .env
```

Replace the placeholder value:

```dotenv
GROQ_API_KEY=your_real_groq_api_key
```

To enable LangSmith locally, also set:

```dotenv
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your_real_langsmith_api_key
LANGSMITH_PROJECT=ali-raza-assistant
```

If PostgreSQL port `5432` is already occupied, use another host port without
changing the container's internal database port:

```dotenv
POSTGRES_PORT=5433
```

Build and start the complete stack:

```powershell
docker compose up --build
```

Open:

- Frontend: <http://localhost:3000>
- Backend health: <http://localhost:8000/api/health>
- API documentation: <http://localhost:8000/docs>

Docker Compose starts PostgreSQL, waits for it to become healthy, applies
Aerich migrations, starts FastAPI, and then starts the frontend.

Stop the stack:

```powershell
docker compose down
```

To also permanently delete the local PostgreSQL volume:

```powershell
docker compose down -v
```

## Local development

### 1. Start PostgreSQL

```powershell
docker compose up -d db
```

### 2. Start the backend

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
Copy-Item ..\.env.example .env
```

Add your Groq API key to `backend/.env`, then run the migrations and API:

```powershell
python -m aerich upgrade
python -m uvicorn app.main:app --reload --port 8000
```

Use `python -m uvicorn` instead of the bare `uvicorn` launcher if a virtual
environment was moved from another directory.

### 3. Start the frontend

Open a second terminal:

```powershell
cd frontend
Copy-Item .env.example .env.local
npm install
npm run dev
```

The frontend expects the API at `http://localhost:8000/api` by default.

## Environment variables

| Variable | Used by | Purpose |
| --- | --- | --- |
| `GROQ_API_KEY` | Backend | Groq authentication; never expose it in the frontend |
| `GROQ_MODEL` | Backend | Model identifier; defaults to `openai/gpt-oss-120b` |
| `TEMPERATURE` | Backend | Model sampling temperature |
| `DATABASE_URL` | Backend | PostgreSQL connection string |
| `GENERATE_SCHEMAS` | Backend | Local-only schema generation switch; production uses migrations |
| `CORS_ORIGINS` | Backend | Comma-separated allowed frontend origins |
| `LANGSMITH_TRACING` | Backend | Enables LangSmith tracing when an API key is present |
| `LANGSMITH_API_KEY` | Backend | Secret LangSmith API key |
| `LANGSMITH_PROJECT` | Backend | LangSmith project receiving traces |
| `LANGSMITH_ENDPOINT` | Backend | LangSmith API endpoint |
| `LANGSMITH_INCLUDE_USER_EMAIL` | Backend | Includes a verified email in trace metadata; defaults to `false` |
| `GOOGLE_CLIENT_ID` | Backend | OAuth web client ID used to verify Google ID tokens |
| `NEXT_PUBLIC_API_URL` | Frontend | Public backend base URL ending in `/api` |
| `NEXT_PUBLIC_GOOGLE_CLIENT_ID` | Frontend | The same OAuth web client ID; safe to expose publicly |
| `POSTGRES_*` | Docker Compose | Local PostgreSQL container settings |
| `BACKEND_PORT` | Docker Compose | Backend host port |
| `FRONTEND_PORT` | Docker Compose | Frontend host port |

Never commit `.env`, `.env.local`, database credentials, or API keys.

## LangSmith observability and threads

Every model turn is traced with the database conversation UUID as its
`thread_id`. This makes all turns in a chat appear together in LangSmith while
preserving a direct lookup from a LangSmith thread to the application
conversation. Trace metadata also includes:

- `conversation_id`, `conversation_title`, and a readable `thread_label`
- `user_id`, `user_display_name`, and `identity_source`
- `device_id` and the browser-generated `device_label`
- `user_email` only when Google verified it and
  `LANGSMITH_INCLUDE_USER_EMAIL=true`

The browser cannot read the computer's real hostname. It creates a random ID
in local storage and a label such as `Windows - Chrome - ed239a`; clearing site
data creates a new anonymous identity. This is deliberately lightweight and
does not attempt invasive device fingerprinting.

To use tracing:

1. Create a LangSmith API key and set the three `LANGSMITH_*` values shown
   above.
2. Restart or redeploy the backend and confirm `/api/health` reports
   `observability.enabled: true`.
3. Send a message, open the `ali-raza-assistant` project in LangSmith, and view
   its Threads page.
4. Search trace metadata by `thread_id`, `thread_label`, `user_id`, or
   `device_label`.

LangSmith receives prompts and model responses when tracing is on. Update your
privacy notice and retention settings before enabling it for public users.

## Optional Google identity

Google identity requires explicit user sign-in; a website cannot silently read
the active Gmail account. To enable the sign-in button:

1. In Google Cloud, configure the OAuth consent screen and create an OAuth 2.0
   **Web application** client ID.
2. Add `http://localhost:3000` and your Vercel domain as authorized JavaScript
   origins.
3. Set that same client ID as `GOOGLE_CLIENT_ID` on the backend and
   `NEXT_PUBLIC_GOOGLE_CLIENT_ID` on the frontend.
4. Redeploy both services and use **Continue with Google** in the sidebar.

The frontend sends the short-lived Google ID token to FastAPI. FastAPI verifies
it, then uses Google's stable `sub` claim as `user_id`. The token itself is
never added to LangSmith metadata or browser local storage. See Google's
[web client ID setup](https://developers.google.com/identity/gsi/web/guides/get-google-api-clientid)
and [server-side ID token verification](https://developers.google.com/identity/gsi/web/guides/verify-google-id-token)
guides.

## Aerich migration workflow

Tortoise models are defined in `backend/app/models/entities.py`. After changing
the database models, run:

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python -m aerich migrate --name describe_your_change
python -m aerich upgrade
```

Useful commands:

```powershell
python -m aerich history
python -m aerich heads
python -m aerich downgrade
```

Review generated migrations before applying them. An incorrect rename or drop
decision can cause data loss.

## Main API routes

| Method | Route | Purpose |
| --- | --- | --- |
| `GET` | `/api/health` | Service, model, and database status |
| `GET` | `/api/identity` | Resolve the anonymous or verified Google trace identity |
| `GET` | `/api/conversations` | List conversations |
| `POST` | `/api/conversations` | Create a conversation |
| `GET` | `/api/conversations/{id}` | Get a conversation and its messages |
| `PATCH` | `/api/conversations/{id}` | Rename a conversation |
| `DELETE` | `/api/conversations/{id}` | Delete a conversation |
| `POST` | `/api/conversations/{id}/messages` | Send a message and stream the response |
| `POST` | `/api/conversations/{id}/regenerate` | Regenerate the latest assistant response |

## Verification

Backend tests:

```powershell
cd backend
.\venv\Scripts\python.exe -m pytest --basetemp .test-tmp
```

Frontend checks:

```powershell
cd frontend
npm run lint
npm run build
node --test tests/rendered-html.test.mjs
```

Docker configuration:

```powershell
docker compose config
docker compose build
```

## Deployment

The production system uses:

- Vercel for the native Next.js frontend in `frontend/`
- Railway for the Dockerized FastAPI backend in `backend/`
- Railway PostgreSQL for persistent production data
- Aerich as the Railway pre-deployment migration command

Required production values:

```dotenv
# Vercel
NEXT_PUBLIC_API_URL=https://my-assistant-gpt-clone-production.up.railway.app/api

# Railway
DATABASE_URL=${{Postgres.DATABASE_URL}}
CORS_ORIGINS=https://ali-raza-assistant-web.vercel.app
GROQ_MODEL=openai/gpt-oss-120b
GENERATE_SCHEMAS=false
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=ali-raza-assistant
```

Keep `GROQ_API_KEY` and `LANGSMITH_API_KEY` in Railway's encrypted variables and
never place their real values in the repository. Railway runs `python -m aerich upgrade` before each
backend deployment and checks `/api/health` before routing production traffic.

See [DEPLOYMENT.md](DEPLOYMENT.md) for the complete deployment workflow and
[BUILD_GUIDE.md](BUILD_GUIDE.md) for the step-by-step architecture guide.

## Current limitations and recommended next steps

- Add authorization and conversation ownership before supporting multiple users;
  the current Google identity labels traces but does not isolate stored chats.
- Add rate limiting and request-size limits before advertising the public URL.
- Configure PostgreSQL backups and production monitoring.
- Add automated CI checks for backend tests and frontend builds.
- Merge the deployment pull request and track `main` for long-term production releases.

## License

No license has been added yet. Add one before redistributing the project as an
open-source package.
