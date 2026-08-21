# Phase 8: Deployment Plan (Railway + Vercel)

This document outlines the steps required to deploy the Zomato AI Recommender into production. We will use a modern, decoupled deployment strategy:
- **Backend (FastAPI)**: Deployed to Railway via Docker.
- **Frontend (Next.js)**: Deployed to Vercel via their seamless Git integration.

## Proposed Changes

### Backend (Railway)

To run our FastAPI application on Railway, we need to provide a standard Docker environment.

#### [NEW] `Dockerfile`
Create a Dockerfile in the root of the repository to containerize the Python app.
- Base image: `python:3.11-slim`
- Install dependencies from `requirements.txt`.
- Copy `src/`, `config/`, and data over.
- Expose port `8000`.
- CMD to run: `uvicorn src.main:app --host 0.0.0.0 --port $PORT`

#### [NEW] `.dockerignore`
Ignore the `frontend/`, `tests/`, `venv/`, and `.git/` directories so the Docker image stays small.

---

### Frontend (Vercel)

Vercel will natively detect our Next.js application, but we need to remove the hardcoded `localhost` URLs so it can communicate with the new Railway backend.

#### [MODIFY] `frontend/app/page.tsx`
Update all `fetch()` calls to use an environment variable instead of `http://localhost:8000`.
- Before: `fetch("http://localhost:8000/api/locations")`
- After: `fetch(\`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/locations\`)`

#### [NEW] `frontend/.env.local`
Add `.env.local` to `.gitignore` and create a template showing how to set `NEXT_PUBLIC_API_URL`.

---

## Deployment Steps (Manual Action Required)

1. **Push code to GitHub:** Commit the Dockerfile and frontend changes.
2. **Railway:** 
   - Create a new project -> Deploy from GitHub Repo.
   - Go to variables, and set `GROQ_API_KEY`.
   - Wait for build to finish, then go to Settings -> Networking -> Generate Domain. 
   - Copy this URL.
3. **Vercel:**
   - Import the GitHub Repo.
   - Set Root Directory to `frontend`.
   - In Environment Variables, set `NEXT_PUBLIC_API_URL` to the Railway URL you just copied.
   - Deploy.
