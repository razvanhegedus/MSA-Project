"""
AI Concierge Tool Handlers & Definitions (Phase 6).

Implements pure Python callables that integrate with repository/service layers:
1. search_pitches: Filters active pitches by city and surface type.
2. check_slot_availability: Evaluates pitch schedule using [) half-open intervals.
3. draft_booking: Pre-validates availability and computes quotes without DB persistence.
4. find_open_lobbies: Discovers matches looking for extra players (+1).
"""

import uuid
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.base_entities import Booking, Pitch, Venue
from app.models.enums import BookingStatus, ParticipantRole, SurfaceType
from app.repositories.booking_repo import BookingRepository
from app.repositories.match_repo import MatchRepository
from app.schemas.ai import (
    CheckSlotAvailabilityArgs,
    DraftBookingArgs,
    DraftBookingQuote,
    FindOpenLobbiesArgs,
    SearchPitchesArgs,
)
from app.services.booking_service import BookingService


# ──────────────────────────────────────────────────────────────────────────────
# OpenAI / Gemini Function-Calling Tool Definitions
# ──────────────────────────────────────────────────────────────────────────────

AI_TOOLS_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "search_pitches",
            "description": (
                "Search available mini-football pitches in a specific city with optional surface "
                "type and lighting capability filters."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "City name (e.g. 'Reșița', 'Timișoara', 'București').",
                    },
                    "surface": {
                        "type": "string",
                        "enum": [
                            "SYNTHETIC_3G",
                            "INDOOR_TARAFLEX",
                            "NATURAL_GRASS",
                            "HYBRID",
                        ],
                        "description": "Optional pitch surface type filter.",
                    },
                    "has_lights": {
                        "type": "boolean",
                        "description": "Optional filter for evening night-lighting capability.",
                    },
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_slot_availability",
            "description": (
                "Check full-day hourly slot availability for a specific pitch on a given date. "
                "Returns availability matrix with status AVAILABLE, OPEN_LOBBY, or OCCUPIED."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "pitch_id": {
                        "type": "string",
                        "description": "UUID of the pitch.",
                    },
                    "query_date": {
                        "type": "string",
                        "description": "Date in ISO format YYYY-MM-DD.",
                    },
                },
                "required": ["pitch_id", "query_date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "draft_booking",
            "description": (
                "Pre-validate a potential booking reservation and calculate pricing quote without "
                "persisting a confirmed record to the database."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "pitch_id": {
                        "type": "string",
                        "description": "UUID of the pitch to book.",
                    },
                    "start_time": {
                        "type": "string",
                        "description": "Booking start time in ISO 8601 UTC (e.g., '2026-11-05T19:00:00Z').",
                    },
                    "end_time": {
                        "type": "string",
                        "description": "Booking end time in ISO 8601 UTC (e.g., '2026-11-05T20:00:00Z').",
                    },
                },
                "required": ["pitch_id", "start_time", "end_time"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_open_lobbies",
            "description": (
                "Search open matchmaking lobbies looking for extra players (+1 announcements) "
                "or goalkeepers."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "City where the match lobby is scheduled.",
                    },
                    "needed_role": {
                        "type": "string",
                        "enum": ["PLAYER", "GOALKEEPER"],
                        "description": "Optional needed player role.",
                    },
                    "date": {
                        "type": "string",
                        "description": "Optional match date in ISO format YYYY-MM-DD.",
                    },
                },
                "required": ["city"],
            },
        },
    },
]


# ──────────────────────────────────────────────────────────────────────────────
# AITools Dispatcher Class
# ──────────────────────────────────────────────────────────────────────────────


class AITools:
    """Encapsulates tool execution handlers backed by pure async SQLAlchemy queries."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.booking_repo = BookingRepository(session)
        self.match_repo = MatchRepository(session)
        self.booking_service = BookingService(session)

    async def search_pitches(
        self,
        city: str,
        surface: Optional[str] = None,
        has_lights: Optional[bool] = None,
    ) -> List[Dict[str, Any]]:
        """Query pitches in the specified city with optional surface and features filter."""
        validated_args = SearchPitchesArgs(
            city=city,
            surface=surface,
            has_lights=has_lights,
        )

        conditions = [
            func.lower(Venue.city) == validated_args.city.strip().lower(),
            Pitch.is_active.is_(True),
        ]

        if validated_args.surface:
            try:
                surface_enum = SurfaceType(validated_args.surface.upper())
                conditions.append(Pitch.surface_type == surface_enum)
            except ValueError:
                pass

        stmt = (
            select(Pitch)
            .join(Pitch.venue)
            .options(selectinload(Pitch.venue))
            .where(and_(*conditions))
            .order_by(Pitch.name.asc())
        )
        result = await self.session.execute(stmt)
        pitches = result.scalars().all()

        results: List[Dict[str, Any]] = []
        for p in pitches:
            results.append(
                {
                    "pitch_id": str(p.id),
                    "pitch_name": p.name,
                    "venue_name": p.venue.name,
                    "address": p.venue.address,
                    "city": p.venue.city,
                    "surface_type": p.surface_type.value,
                    "team_size_capacity": p.team_size_capacity,
                    "hourly_rate": float(p.hourly_rate),
                    "opening_hour": p.venue.opening_hour,
                    "closing_hour": p.venue.closing_hour,
                    "has_lights": True if validated_args.has_lights is not False else False,
                }
            )
        return results

    async def check_slot_availability(
        self,
        pitch_id: uuid.UUID,
        query_date: date,
    ) -> List[Dict[str, Any]]:
        """Evaluate pitch availability using half-open intervals [)."""
        validated_args = CheckSlotAvailabilityArgs(
            pitch_id=pitch_id,
            query_date=query_date,
        )

        pitch = await self.booking_repo.get_pitch_with_venue(validated_args.pitch_id)
        if not pitch:
            return [{"error": f"Pitch with ID {validated_args.pitch_id} not found."}]

        slots = await self.booking_service.get_daily_availability(
            pitch_id=validated_args.pitch_id,
            target_date=validated_args.query_date,
        )

        return [
            {
                "pitch_id": str(validated_args.pitch_id),
                "pitch_name": pitch.name,
                "venue_name": pitch.venue.name,
                "start_time": s.start_time.isoformat(),
                "end_time": s.end_time.isoformat(),
                "status": s.status,
                "price": float(s.price),
                "spots_left": s.spots_left,
                "open_match_id": str(s.open_match_id) if s.open_match_id else None,
            }
            for s in slots
        ]

    async def draft_booking(
        self,
        pitch_id: uuid.UUID,
        start_time: datetime,
        end_time: datetime,
    ) -> Dict[str, Any]:
        """
        Pre-validate booking constraints and calculate pricing without persisting
        records to the database. Strictly validates half-open [) intervals.
        """
        validated_args = DraftBookingArgs(
            pitch_id=pitch_id,
            start_time=start_time,
            end_time=end_time,
        )

        pitch = await self.booking_repo.get_pitch_with_venue(validated_args.pitch_id)
        if not pitch:
            return {
                "is_available": False,
                "status": "NOT_FOUND",
                "message": f"Pitch with ID {validated_args.pitch_id} does not exist.",
            }

        venue = pitch.venue

        # Ensure UTC timezone awareness
        st = validated_args.start_time
        if st.tzinfo is None:
            st = st.replace(tzinfo=timezone.utc)
        else:
            st = st.astimezone(timezone.utc)

        et = validated_args.end_time
        if et.tzinfo is None:
            et = et.replace(tzinfo=timezone.utc)
        else:
            et = et.astimezone(timezone.utc)

        if et <= st:
            return {
                "is_available": False,
                "status": "INVALID_TIME_RANGE",
                "message": "End time must be strictly after start time.",
            }

        start_hour = st.hour
        end_hour = 24 if (et.hour == 0 and et.day > st.day) else et.hour

        if start_hour < venue.opening_hour or end_hour > venue.closing_hour:
            return {
                "is_available": False,
                "status": "OUTSIDE_OPERATING_HOURS",
                "message": (
                    f"Booking outside venue operating hours "
                    f"({venue.opening_hour}:00 - {venue.closing_hour}:00)."
                ),
            }

        # Check overlapping non-cancelled bookings using [) range overlap
        overlapping = await self.booking_repo.get_overlapping_bookings(
            pitch_id=pitch.id,
            window_start=st,
            window_end=et,
        )

        duration_seconds = (et - st).total_seconds()
        duration_hours = Decimal(str(duration_seconds / 3600))
        total_price = (pitch.hourly_rate * duration_hours).quantize(Decimal("0.01"))

        if overlapping:
            quote = DraftBookingQuote(
                pitch_id=pitch.id,
                pitch_name=pitch.name,
                venue_name=venue.name,
                city=venue.city,
                start_time=st,
                end_time=et,
                duration_hours=duration_hours,
                hourly_rate=pitch.hourly_rate,
                total_price=total_price,
                is_available=False,
                status="SLOT_OCCUPIED",
                message="Requested time interval overlaps with an existing booking.",
            )
        else:
            quote = DraftBookingQuote(
                pitch_id=pitch.id,
                pitch_name=pitch.name,
                venue_name=venue.name,
                city=venue.city,
                start_time=st,
                end_time=et,
                duration_hours=duration_hours,
                hourly_rate=pitch.hourly_rate,
                total_price=total_price,
                is_available=True,
                status="AVAILABLE",
                message="Slot is available for booking.",
            )

        return quote.model_dump(mode="json")

    async def find_open_lobbies(
        self,
        city: str,
        needed_role: Optional[str] = None,
        date_param: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        """Discover open match lobbies looking for extra players."""
        validated_args = FindOpenLobbiesArgs(
            city=city,
            needed_role=needed_role,
            date=date_param,
        )

        role_enum = None
        if validated_args.needed_role:
            try:
                role_enum = ParticipantRole(validated_args.needed_role.upper())
            except ValueError:
                pass

        matches = await self.match_repo.find_open_lobbies(
            city=validated_args.city,
            needed_role=role_enum,
            target_date=validated_args.date,
        )

        results: List[Dict[str, Any]] = []
        for m in matches:
            confirmed = sum(1 for p in m.participants if p.status.value == "CONFIRMED")
            results.append(
                {
                    "match_id": str(m.id),
                    "venue_name": m.booking.pitch.venue.name,
                    "pitch_name": m.booking.pitch.name,
                    "city": m.booking.pitch.venue.city,
                    "scheduled_at": m.scheduled_at.isoformat(),
                    "spots_left": max(0, m.target_players - confirmed),
                    "needed_positions": m.needed_positions or [],
                    "description": m.description or "",
                }
            )
        return results

    async def dispatch_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Route tool invocation by name with raw arguments dictionary."""
        if tool_name == "search_pitches":
            return await self.search_pitches(
                city=arguments.get("city", ""),
                surface=arguments.get("surface"),
                has_lights=arguments.get("has_lights"),
            )
        elif tool_name == "check_slot_availability":
            raw_pitch_id = arguments["pitch_id"]
            pitch_uuid = uuid.UUID(str(raw_pitch_id)) if not isinstance(raw_pitch_id, uuid.UUID) else raw_pitch_id
            raw_date = arguments["query_date"]
            parsed_date = date.fromisoformat(str(raw_date)) if isinstance(raw_date, str) else raw_date
            return await self.check_slot_availability(
                pitch_id=pitch_uuid,
                query_date=parsed_date,
            )
        elif tool_name == "draft_booking":
            raw_pitch_id = arguments["pitch_id"]
            pitch_uuid = uuid.UUID(str(raw_pitch_id)) if not isinstance(raw_pitch_id, uuid.UUID) else raw_pitch_id
            st = arguments["start_time"]
            start_dt = datetime.fromisoformat(str(st).replace("Z", "+00:00")) if isinstance(st, str) else st
            et = arguments["end_time"]
            end_dt = datetime.fromisoformat(str(et).replace("Z", "+00:00")) if isinstance(et, str) else et
            return await self.draft_booking(
                pitch_id=pitch_uuid,
                start_time=start_dt,
                end_time=end_dt,
            )
        elif tool_name == "find_open_lobbies":
            raw_date = arguments.get("date")
            parsed_date = date.fromisoformat(str(raw_date)) if isinstance(raw_date, str) and raw_date else None
            return await self.find_open_lobbies(
                city=arguments.get("city", ""),
                needed_role=arguments.get("needed_role"),
                date_param=parsed_date,
            )
        else:
            return [{"error": f"Unknown tool: {tool_name}"}]
