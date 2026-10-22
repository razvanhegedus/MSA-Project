# Antigravity Agent Guidelines — Pitch Platform

You are an Autonomous Software Engineering Agent in Google Antigravity building `pitch-platform`, a high-concurrency mini-football pitch booking, matchmaking (+1 open lobbies), tournament management, and AI concierge platform.

Always treat `@[project_spec](project_spec.md)` as the authoritative contract for database schemas, DTOs, directory paths, and verification tests.

---

## 1. Operating Modes & Autonomy Protocol

1. **Plan Before Executing:**
   - Before applying file modifications, generate a structured artifact outlining the exact files to be created/edited and the terminal verification commands you intend to run.
   - Execute strictly phase-by-phase following Section G of `project_spec.md`. Do not anticipate or jump ahead to unrequested phases.
2. **Terminal Execution Discipline:**
   - Execute non-interactive CLI commands directly using your terminal capabilities.
   - Always run verification gates immediately after generating phase code (e.g., `docker compose exec`, `alembic upgrade head`, `pytest`).
   - If a terminal command returns a non-zero exit code or traceback, inspect the error output, modify the offending files, and re-run until all tests/migrations pass before completing your turn.
3. **Completeness Invariant:**
   - Never generate placeholders, truncated ellipsis snippets (`// ... rest of code`), or unfinished `TODO` blocks.
   - All generated code must be complete, runnable, and syntactically valid.

---

## 2. Backend Stack & Standards (`/backend`)

- **Runtime & Framework:** Python 3.12+, FastAPI (100% async endpoint definitions and dependencies).
- **ORM & Driver:** SQLAlchemy 2.0+ async (`sqlalchemy.ext.asyncio.AsyncSession`, `create_async_engine`) with `asyncpg`.
- **Database:** PostgreSQL 16+ with extensions `uuid-ossp` and `btree_gist` enabled in migration 0001.
- **Validation:** Pydantic v2 exclusively (`pydantic-settings`, `ConfigDict(from_attributes=True)`, `@model_validator(mode="after")`).
- **Strict 4-Tier Architecture:**
  1. `app/api/v1/*.py`: HTTP routes, query params, dependency injection (`Depends(get_db)`, `Depends(get_current_user)`). No direct DB queries.
  2. `app/services/*.py`: Business logic, pricing, operating-hour validation, AI tool execution, transaction control (`session.commit()` / `session.rollback()`), and exception translation into domain errors (`app/core/exceptions.py`).
  3. `app/repositories/*.py`: Pure SQLAlchemy 2.0 select/insert queries using `session.flush()`.
  4. `app/models/*.py`: Declarative entities inheriting from `DeclarativeBase`.

---

## 3. Critical Database & Concurrency Rules

- **SQLAlchemy 2.0 Syntax Only:**
  - Always use `Mapped[T]` and `mapped_column(...)`.
  - **FORBIDDEN:** Legacy SQLAlchemy 1.x `Column(...)` syntax or `session.query(...)`.
  - Use `selectinload()` or `joinedload()` on relationships in async queries to prevent lazy-load greenlet exceptions.
- **Hardware-Level Double-Booking Prevention (Phase 4):**
  - The `bookings` table MUST enforce the PostgreSQL `btree_gist` exclusion constraint:
    ```sql
    CONSTRAINT excl_bookings_no_overlap EXCLUDE USING gist (
        pitch_id WITH =,
        tstzrange(start_time, end_time, '[)') WITH &&
    ) WHERE (status != 'CANCELLED')
    ```
  - Always use the half-open interval `'[)'` to permit seamless back-to-back bookings.
  - In `BookingService.create_booking`, catch `sqlalchemy.exc.IntegrityError` and check for SQLSTATE `23P01` or `excl_bookings_no_overlap` to raise `SlotAlreadyBookedError` (HTTP 409).
- **Match Lobby Locking (Phase 5):**
  - When a user joins a match, always lock the match record using `.with_for_update()` (`SELECT ... FOR UPDATE`).
  - Check player capacity inside the lock transaction and update `match.status = MatchStatus.FULL` atomically when target capacity is reached.
- **Timestamps & Numbers:**
  - All timestamps must be timezone-aware (`TIMESTAMPTZ` / `datetime.now(timezone.utc)`).
  - All money fields (`hourly_rate`, `total_price`, `entry_fee`) must use `Numeric(10, 2)` / Python `Decimal`.

---

## 4. Frontend & Mobile-First Standards (`/frontend`)

- **Framework:** React 19 + TypeScript (Vite bundler), Tailwind CSS, Lucide icons.
- **Mobile-First Layout:**
  - Mobile frame target (`max-w-md mx-auto` shell, bottom navigation, slide-up drawers).
- **Slot Matrix States (`TimeSlotSelector.tsx`):**
  - `AVAILABLE`: Green pill / card (`bg-emerald-50`, allows booking selection).
  - `OPEN_LOBBY`: Amber / Orange (`bg-amber-50`, shows spots left badge, opens join match flow).
  - `OCCUPIED`: Slate grey (`bg-slate-100`, disabled with lock icon).
- **Client & State:**
  - Axios client (`src/api/client.ts`) with automatic Bearer token injection and refresh interceptor.
  - TanStack Query v5 hooks (`useQuery`, `useMutation`) with cache invalidation on booking mutations.
  - Keep `frontend/src/types/api.ts` strictly synchronized with backend Pydantic models.

---

## 5. Phase-by-Phase Verification Commands

When executing a phase, run and verify the corresponding shell command:

- **Phase 1 (Infra):**
  `docker compose up -d db && docker compose exec db psql -U postgres -c "SELECT version();"`
- **Phase 2 (Models & Migrations):**
  `cd backend && alembic upgrade head && docker compose exec db psql -U postgres -d pitch_db -c "\d bookings"`
- **Phase 3 (Auth):**
  `cd backend && uvicorn app.main:app --reload` (Test `/api/v1/auth/register` and `/api/v1/auth/login`)
- **Phase 4 (Booking Concurrency Test):**
  `cd backend && pytest tests/test_booking_concurrency.py -v` (10 parallel requests -> 1 HTTP 201, 9 HTTP 409)
- **Phase 5 (Lobby Lock Concurrency Test):**
  `cd backend && pytest tests/test_match_concurrency.py -v` (5 parallel joins on 1 spot -> 1 HTTP 200, 4 HTTP 409)
- **Phase 6 (AI Tool Calling):**
  `curl -X POST http://localhost:8000/api/v1/ai/chat -H "Content-Type: application/json" -d '{"message": "Find me a synthetic pitch in Reșița tomorrow at 20:00"}'`
- **Phase 7 (Frontend Build):**
  `cd frontend && npm install && npm run build` (Must complete with 0 TypeScript/ESLint errors)