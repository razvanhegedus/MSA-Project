# Running Pitch Platform Locally

This guide walks you through setting up and running the Pitch Platform (PostgreSQL database, FastAPI backend, and React/Vite frontend) on your local machine.

---

## Prerequisites

Ensure you have the following installed:
- **Docker & Docker Compose** (for PostgreSQL 16)
- **Python 3.11+** with [`uv`](https://docs.astral.sh/uv/) (recommended) or `pip` / `venv`
- **Node.js 18+** & **npm** (for the frontend)

---

## 1. Start the Database (PostgreSQL 16)

Pitch Platform requires PostgreSQL 16 with the `btree_gist` extension (used for hardware-level double-booking exclusion constraints).

From the project root:

```bash
docker compose up -d db
```

Verify that the container is running and healthy:

```bash
docker ps
```
You should see `pitch_db` running on `0.0.0.0:5432->5432/tcp` with status `(healthy)`.

---

## 2. Start the Backend API (FastAPI)

### 2.1 Environment Configuration
Navigate to the `backend/` directory:
```bash
cd backend
```

If not already present, create `.env` from `.env.example`:
```bash
cp .env.example .env
```

Ensure your database connection string in `.env` matches:
```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/pitch_db
DATABASE_URL_SYNC=postgresql://postgres:postgres@localhost:5432/pitch_db
```

*(Optional)* If you plan to use the AI concierge assistant, set your LLM credentials:
```env
LLM_API_KEY=your_api_key_here
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL_NAME=gpt-4o
```

### 2.2 Run Database Migrations
Apply Alembic migrations to set up schema tables and constraints:

```bash
uv run alembic upgrade head
```
*(Or activate your virtualenv and run `alembic upgrade head`)*

### 2.3 Start the FastAPI Server
Run the backend with hot reloading enabled:

```bash
uv run uvicorn app.main:app --reload --port 8000
```

- **API Base URL**: [http://localhost:8000](http://localhost:8000)
- **Interactive Swagger Docs**: [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs)
- **ReDoc Documentation**: [http://localhost:8000/api/v1/redoc](http://localhost:8000/api/v1/redoc)

---

## 3. Start the Frontend (Vite + React)

Open a **separate terminal window** and run:

### 3.1 Navigate to Frontend & Install Dependencies
```bash
cd frontend
npm install
```

### 3.2 Launch Development Server
```bash
npm run dev
```

- **Frontend App**: [http://localhost:5173](http://localhost:5173)

> **API Proxying**: Vite is configured in `vite.config.ts` to automatically proxy all `/v1` requests to `http://localhost:8000/api`, routing requests to the FastAPI backend without CORS configuration issues.

---

## 4. Running Backend Tests

To run the automated test suite (including concurrency and exclusion constraint verification):

```bash
cd backend
uv run pytest
```

---

## Quick Reference Summary

| Service | Command | URL |
| :--- | :--- | :--- |
| **PostgreSQL 16** | `docker compose up -d db` | `localhost:5432` |
| **Backend API** | `cd backend && uv run uvicorn app.main:app --reload --port 8000` | [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs) |
| **Frontend Web** | `cd frontend && npm run dev` | [http://localhost:5173](http://localhost:5173) |
| **Tests** | `cd backend && uv run pytest` | - |

