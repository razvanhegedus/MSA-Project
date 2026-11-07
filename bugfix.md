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