# Deploying Ali Raza's Assistant

The production architecture is:

- Vercel: native Next.js frontend from `frontend/`
- Railway: FastAPI backend from `backend/`
- Railway PostgreSQL: managed production database
- GitHub: source for automatic deployments

## 1. Deploy the Railway backend

Create a Railway project from the GitHub repository and set the service root
directory to `/backend`. Set the Railway configuration file path to
`/backend/railway.json`.

Add a Railway PostgreSQL service to the project. In the backend service, add
these variables:

    DATABASE_URL=${{Postgres.DATABASE_URL}}
    GROQ_API_KEY=your_real_groq_api_key
    GROQ_MODEL=openai/gpt-oss-120b
    TEMPERATURE=0.2
    APP_ENV=production
    GENERATE_SCHEMAS=false
    CORS_ORIGINS=https://your-vercel-domain.vercel.app

If the database service has a different name, replace `Postgres` in the
reference with that service name. Do not paste the database password or Groq
key into the repository.

Railway builds `backend/Dockerfile`, runs `python -m aerich upgrade` before
each deployment, checks `/api/health`, and supplies its assigned `PORT` to the
container. Generate a public domain for the backend and verify:

    https://your-backend.up.railway.app/api/health

## 2. Deploy the Vercel frontend

Import the same GitHub repository in Vercel. Configure:

- Framework preset: Next.js
- Root directory: `frontend`
- Build command: `npm run build`
- Output directory: leave empty (Next.js default)
- Install command: `npm ci`

Set this environment variable for Production, Preview, and Development:

    NEXT_PUBLIC_API_URL=https://your-backend.up.railway.app/api

Deploy the project. Copy the assigned production domain, then update the
Railway backend's `CORS_ORIGINS` variable to that exact origin without a
trailing slash. Railway will redeploy the backend automatically.

## 3. Production verification

Check all of the following:

1. Railway `/api/health` returns `status: ok` and `database: connected`.
2. The Vercel site loads without browser console errors.
3. Creating a chat returns a streamed assistant response.
4. Refreshing the page preserves the conversation from PostgreSQL.
5. Renaming and deleting a conversation work.

## Deployment updates

After the GitHub branch is connected, changes under `frontend/` deploy to
Vercel and changes under `backend/` deploy to Railway. Aerich migrations are
applied by Railway before the new backend version receives traffic.

For local Docker development, `frontend/Dockerfile` continues using Vinext;
the normal `npm run build` command is reserved for Vercel's native Next.js
build.
