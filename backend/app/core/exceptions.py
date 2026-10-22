from fastapi import HTTPException, status


class DomainError(HTTPException):
    pass


class SlotAlreadyBookedError(DomainError):
    def __init__(self, detail: str = "This pitch is already booked for the requested time window."):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class LobbyFullError(DomainError):
    def __init__(self, detail: str = "This match lobby has reached maximum player capacity."):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class AlreadyJoinedError(DomainError):
    def __init__(self, detail: str = "User is already registered in this match lobby."):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class ResourceNotFoundError(DomainError):
    def __init__(self, resource: str):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=f"{resource} not found.")
