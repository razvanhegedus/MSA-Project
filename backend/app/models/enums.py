import enum


class UserRole(str, enum.Enum):
    PLAYER = "PLAYER"
    VENUE_OWNER = "VENUE_OWNER"
    ADMIN = "ADMIN"


class SurfaceType(str, enum.Enum):
    SYNTHETIC_3G = "SYNTHETIC_3G"
    INDOOR_TARAFLEX = "INDOOR_TARAFLEX"
    NATURAL_GRASS = "NATURAL_GRASS"
    HYBRID = "HYBRID"


class BookingStatus(str, enum.Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"


class MatchType(str, enum.Enum):
    OPEN_LOBBY = "OPEN_LOBBY"
    SQUAD_CHALLENGE = "SQUAD_CHALLENGE"
    TOURNAMENT_MATCH = "TOURNAMENT_MATCH"


class MatchStatus(str, enum.Enum):
    OPEN = "OPEN"
    FULL = "FULL"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"


class TeamSide(str, enum.Enum):
    A = "A"
    B = "B"


class ParticipantRole(str, enum.Enum):
    ORGANIZER = "ORGANIZER"
    PLAYER = "PLAYER"
    GOALKEEPER = "GOALKEEPER"


class ParticipantStatus(str, enum.Enum):
    CONFIRMED = "CONFIRMED"
    PENDING = "PENDING"


class TournamentFormat(str, enum.Enum):
    SINGLE_ELIMINATION = "SINGLE_ELIMINATION"
    GROUP_AND_KNOCKOUT = "GROUP_AND_KNOCKOUT"


class TournamentStatus(str, enum.Enum):
    REGISTRATION_OPEN = "REGISTRATION_OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
