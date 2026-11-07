import uuid
from datetime import date
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import LobbyFullError, AlreadyJoinedError, ResourceNotFoundError
from app.models.base_entities import Match, MatchParticipant
from app.models.enums import BookingStatus, MatchStatus, MatchType, ParticipantRole, ParticipantStatus, TeamSide
from app.repositories.booking_repo import BookingRepository
from app.repositories.match_repo import MatchRepository
from app.schemas.match import MatchCreateRequest, MatchDetailResponse, MatchJoinRequest, MatchParticipantResponse


class MatchService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = MatchRepository(session)
        self.booking_repo = BookingRepository(session)

    async def create_match(
        self, user_id: uuid.UUID, payload: MatchCreateRequest
    ) -> MatchDetailResponse:
        booking = await self.booking_repo.get_booking_by_id(payload.booking_id)
        if not booking:
            raise ResourceNotFoundError("Booking")

        if booking.booked_by_user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the user who reserved the booking can create a match lobby for it.",
            )

        if booking.status != BookingStatus.CONFIRMED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot create a match for a non-confirmed booking.",
            )

        existing_match = await self.repo.get_match_by_booking_id(payload.booking_id)
        if existing_match:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A match is already linked to this booking.",
            )

        match = Match(
            booking_id=payload.booking_id,
            organizer_id=user_id,
            match_type=payload.match_type,
            target_players=payload.target_players,
            needed_positions=payload.needed_positions or [],
            description=payload.description,
            status=MatchStatus.OPEN,
            scheduled_at=booking.start_time,
        )
        await self.repo.create_match(match)

        organizer = MatchParticipant(
            match_id=match.id,
            user_id=user_id,
            team_side=TeamSide.A,
            role=ParticipantRole.ORGANIZER,
            status=ParticipantStatus.CONFIRMED,
        )
        await self.repo.add_participant(organizer)
        await self.session.commit()

        return await self.get_match(match.id)

    async def join_match(
        self, match_id: uuid.UUID, user_id: uuid.UUID, payload: MatchJoinRequest
    ) -> MatchDetailResponse:
        # Step 1: Lock the match row using SELECT ... FOR UPDATE
        match = await self.repo.get_match_for_update(match_id)
        if not match:
            raise ResourceNotFoundError("Match")

        if match.status != MatchStatus.OPEN:
            raise LobbyFullError(f"Cannot join match with status {match.status.value}.")

        # Step 2: Check if user is already a participant
        if any(p.user_id == user_id for p in match.participants):
            raise AlreadyJoinedError()

        # Step 3: Count confirmed players while holding the row lock
        confirmed_players = [
            p for p in match.participants if p.status == ParticipantStatus.CONFIRMED
        ]
        if len(confirmed_players) >= match.target_players:
            match.status = MatchStatus.FULL
            await self.session.commit()
            raise LobbyFullError()

        # Step 4: Insert participant & transition lobby status if last slot was claimed
        new_participant = MatchParticipant(
            match_id=match.id,
            user_id=user_id,
            team_side=payload.team_side,
            role=payload.role,
            status=ParticipantStatus.CONFIRMED,
        )
        match.participants.append(new_participant)

        if len(confirmed_players) + 1 >= match.target_players:
            match.status = MatchStatus.FULL

        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise AlreadyJoinedError() from exc

        # Discard stale cached relationships in session identity map so get_match_by_id loads fresh data
        self.session.expire_all()
        updated_match = await self.repo.get_match_by_id(match_id)
        return self._to_detail_response(updated_match)

    async def get_match(self, match_id: uuid.UUID) -> MatchDetailResponse:
        match = await self.repo.get_match_by_id(match_id)
        if not match:
            raise ResourceNotFoundError("Match")
        return self._to_detail_response(match)

    async def find_open_lobbies(
        self,
        city: Optional[str] = None,
        needed_role: Optional[str] = None,
        target_date: Optional[date] = None,
        match_type: Optional[MatchType] = None,
    ) -> List[MatchDetailResponse]:
        matches = await self.repo.find_open_lobbies(
            city=city,
            needed_role=needed_role,
            target_date=target_date,
            match_type=match_type,
        )
        return [self._to_detail_response(m) for m in matches]

    @staticmethod
    def _to_detail_response(match: Match) -> MatchDetailResponse:
        pitch = match.booking.pitch
        venue = pitch.venue
        confirmed_count = sum(
            1 for p in match.participants if p.status == ParticipantStatus.CONFIRMED
        )
        participants_dto = [
            MatchParticipantResponse(
                id=p.id,
                user_id=p.user_id,
                full_name=p.user.full_name if p.user else "Player",
                team_side=p.team_side,
                role=p.role,
                status=p.status,
                joined_at=p.joined_at,
            )
            for p in match.participants
        ]
        return MatchDetailResponse(
            id=match.id,
            booking_id=match.booking_id,
            organizer_id=match.organizer_id,
            match_type=match.match_type,
            target_players=match.target_players,
            current_players_count=confirmed_count,
            needed_positions=match.needed_positions,
            description=match.description,
            status=match.status,
            scheduled_at=match.scheduled_at,
            venue_name=venue.name,
            pitch_name=pitch.name,
            city=venue.city,
            participants=participants_dto,
        )
