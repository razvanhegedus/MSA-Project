# Pitch Platform — Bugfix Specification & Architecture Plan

## 1. Overview of Reported Issues
1. **Pitch Details Gallery Images:** Main image and thumbnails overflow the container, breaking into adjacent UI elements; one Unsplash URL is broken (404/broken image).
2. **Bookings Not Showing in "My Bookings" Tab:** Route path mismatch (`/bookings/my` vs `/bookings/me`) returns HTTP 422; missing TanStack Query cache invalidation for `['user-bookings']`.
3. **Match Joining & Cache Sync:** Joining a match does not refresh the pitch availability matrix or remaining spot badges; errors are swallowed silently; modal role picker includes invalid backend role `ORGANIZER`.
4. **Player Position & Role Filtering:** Matches page only filters for Goalkeepers, missing Defender, Midfielder, Forward positions; backend performs exact enum matching instead of position substring matching.
5. **AI Assistant Failure:** Missing/dummy LLM API keys cause unhandled 500 exceptions with no fallback; frontend crashes if `result_summary` is a dictionary rather than an array; no UI error handling.

---

## 2. Root Cause Analysis & Target Files

### Step 1: Booking Endpoints & Cache Sync
- **Backend:** `backend/app/api/v1/bookings.py` defines `@router.get("/bookings/me")`. When frontend requests `/bookings/my`, FastAPI interprets `"my"` as a `booking_id` UUID parameter and raises a 422 error.
- **Frontend:** `frontend/src/api/bookings.ts` calls `/bookings/my` and fails to invalidate `['user-bookings']` in `useCreateBooking`.

### Step 2: Pitch Detail Gallery Layout
- **Frontend:** `frontend/src/pages/PitchDetailPage.tsx` lacks `min-h-0` and overflow bounds on the grid thumbnail buttons, causing high-resolution Unsplash assets to expand grid tracks far beyond `h-80`.
- **Frontend:** `frontend/src/components/pitch/PitchCard.tsx` and `PitchDetailPage.tsx` contain a broken Unsplash image URL (`photo-1508098682722-e99c43a406b2`).

### Step 3: Match Joining & Position Expansions
- **Backend:** `backend/app/repositories/match_repo.py`, `match_service.py`, and `matches.py` only allow `needed_role` as a `ParticipantRole` enum, failing against flexible position tags in `needed_positions`.
- **Frontend:** `frontend/src/components/match/JoinMatchModal.tsx` exposes `ORGANIZER` instead of playing positions.
- **Frontend:** `frontend/src/pages/MatchesPage.tsx` and `PitchDetailPage.tsx` have no error feedback when joining fails and fail to invalidate `['pitch-availability']`.

### Step 4: AI Concierge Resilience & Tool Rendering
- **Backend:** `backend/app/services/ai_concierge_service.py` lacks an exception fallback when `client.chat.completions.create` encounters missing credentials or API errors.
- **Frontend:** `frontend/src/components/ai/AIChatDrawer.tsx` and `frontend/src/pages/AIAssistantPage.tsx` attempt `.map()` on `tool.result_summary` even if it is a single object (e.g. `draft_booking`).

### Step 5: Test Suite Expansion
- **Backend:** Add dedicated test coverage in `test_booking_concurrency.py`, `test_match_concurrency.py`, and `test_ai_concierge.py`.

---

## 3. Follow-up Implementation

### Existing Foundation

The original implementation by Razvan used PostgreSQL 16 with a GiST exclusion constraint on half-open booking intervals. FastAPI serves the API, and the booking service owns each transaction. The match service uses a row lock when a player joins so concurrent requests cannot take the same final place. The React frontend already used a shared date strip and time-slot cards to book a pitch. This update builds on those pieces. [Initial schema](backend/alembic/versions/0001_initial_schema.py) · [Booking service](backend/app/services/booking_service.py) · [Match service](backend/app/services/match_service.py)

- The earlier bugfix corrected the My Bookings route and cache, repaired the pitch gallery, improved lobby filtering and join errors, and added a local fallback for the AI concierge. [c94a3bc](https://github.com/razvanhegedus/MSA-Project/commit/c94a3bc)
- The next revision added Romanian demo data, pitch deduplication, past-slot handling, and profile controls for creating and editing match lobbies. [3870376](https://github.com/razvanhegedus/MSA-Project/commit/3870376)

### Step 1. Reservation Management

Under **Profile → Upcoming**, players can choose **Move to another slot** or **Cancel reservation**. A move keeps the booking ID, pitch, duration, and total price. It moves an active linked lobby to the new time with its roster intact. Cancellation frees the slot, cancels the linked lobby, and keeps a **Cancelled** entry in **History**. [Profile](frontend/src/pages/ProfilePage.tsx) · [Reservation dialog](frontend/src/components/booking/ManageReservationDialog.tsx)

| Endpoint | Behavior |
| --- | --- |
| `GET /api/v1/bookings/{booking_id}/availability?target_date=YYYY-MM-DD` | Returns the hourly availability matrix for the same pitch with the current reservation excluded from the overlap check. |
| `PATCH /api/v1/bookings/{booking_id}` | Accepts an ISO 8601 `start_time` and returns the updated booking. The service derives the end time from the existing duration. |
| `DELETE /api/v1/bookings/{booking_id}` | Marks the booking and linked lobby as cancelled and returns the booking. Repeating the request returns the cancelled booking. |

The booker can manage an upcoming reservation. Reading reservation details is restricted to the booker, the venue owner, or an administrator. The service locks the booking and its linked lobby while it applies a move or cancellation. A slot conflict returns HTTP 409 and leaves the original reservation and lobby intact. The existing exclusion constraint protects against concurrent requests for the same slot. [Booking routes](backend/app/api/v1/bookings.py) · [Booking repository](backend/app/repositories/booking_repo.py) · [Booking service](backend/app/services/booking_service.py)

### Step 2. Availability, Lobbies, and Data Validation

- Availability uses half-open overlap checks so partially occupied periods appear unavailable and back-to-back bookings can meet at the same boundary. Checkout, rescheduling, and AI booking drafts share UTC normalization and exact venue-hour validation, including a closing time of midnight. [Booking rules](backend/app/core/booking_rules.py) · [AI tools](backend/app/services/ai_tools.py)
- Matchmaking filters out lobbies that have started. The server checks the start time again on join and refuses new lobbies for past bookings. A full lobby keeps its capacity when the organizer edits only its details. Its direct link opens the requested lobby, including full lobbies and squad challenges. [Match repository](backend/app/repositories/match_repo.py) · [Match service](backend/app/services/match_service.py) · [Matches page](frontend/src/pages/MatchesPage.tsx)
- Tournament registration locks the tournament before counting teams, so only one request can claim the final place. Partial venue-hour changes are validated together with the stored values under a venue lock. Invalid hours return HTTP 422. [Tournament service](backend/app/services/tournament_service.py) · [Venue service](backend/app/services/venue_service.py)

### Step 3. Account Layout and Session State

- Profile aligns the account panel, activity tabs, booking metadata, and reservation actions across screen sizes. The move dialog reuses `DateScroller` and `TimeSlotSelector` from pitch booking. Only windows with enough consecutive free hours can be selected. A date jump reaches dates beyond the visible strip. [Profile](frontend/src/pages/ProfilePage.tsx) · [Date strip](frontend/src/components/booking/DateScroller.tsx) · [Time cards](frontend/src/components/booking/TimeSlotSelector.tsx)
- My Bookings and My Matches use account-specific query keys. Ending a session clears the private queries. The Axios client shares concurrent refresh requests within one session and rejects stale authenticated responses after an account switch. Invalid sign-in credentials stay on the form, and sign-in preserves the intended redirect. [Booking hooks](frontend/src/api/bookings.ts) · [Match hooks](frontend/src/api/matches.ts) · [Auth context](frontend/src/context/AuthContext.tsx) · [API client](frontend/src/api/client.ts)
- Successful reservation changes update the booking list and refresh pitch availability and affected match queries. A conflict during a move refreshes the available times so the player can pick another slot. [Reservation dialog](frontend/src/components/booking/ManageReservationDialog.tsx) · [Booking hooks](frontend/src/api/bookings.ts)

### Step 4. Frontend Checks and Serving

ESLint runs with a flat configuration for TypeScript and React Hooks. The frontend image includes an nginx template that proxies `/v1/` to the backend and serves React Router deep links through `index.html`. Set `API_UPSTREAM` for the intended backend. The Docker build context excludes local dependencies, build output, and environment files. [ESLint](frontend/eslint.config.js) · [nginx template](frontend/nginx/default.conf.template) · [Running guide](RUNNING.md#serve-the-production-frontend-with-nginx)

### Verification

With `DATABASE_URL` pointing to a separate PostgreSQL 16 test database, run from `backend/`.

```bash
uv run --locked --extra dev --no-install-project alembic upgrade head
uv run --locked --extra dev --no-install-project python -m pytest -q
```

Run from `frontend/`.

```bash
npm ci
npm run lint
npm run build
```

The PostgreSQL suite passed 40 tests, including reservation ownership, overlapping moves, rollback, cancellation, rebooking, and concurrent updates. Frontend lint and the production build passed. Chrome verified the Profile and shared picker at widths from 320px to 1440px, a two-hour move, the regular booking picker, and cancellation. The rendered nginx configuration passed `nginx -t` and browser checks for deep links and API proxying on a host without Docker. The frontend image build requires a Docker environment. [Reservation management tests](backend/tests/test_booking_management.py) · [Service regression tests](backend/tests/test_service_regressions.py)
