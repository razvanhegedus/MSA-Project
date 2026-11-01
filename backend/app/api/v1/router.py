from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.venues import router as venues_router
from app.api.v1.bookings import router as bookings_router
from app.api.v1.matches import router as matches_router
from app.api.v1.tournaments import router as tournaments_router

api_v1_router = APIRouter()

# Mount auth routes under /auth
api_v1_router.include_router(auth_router, prefix="/auth", tags=["auth"])

# Mount venues routes under /venues
api_v1_router.include_router(venues_router, prefix="/venues", tags=["venues"])

# Mount bookings and pitch availability routes
api_v1_router.include_router(bookings_router, tags=["bookings"])

# Mount match lobbies and matchmaking routes under /matches
api_v1_router.include_router(matches_router, prefix="/matches", tags=["matches"])

# Mount tournaments routes under /tournaments
api_v1_router.include_router(tournaments_router, prefix="/tournaments", tags=["tournaments"])
