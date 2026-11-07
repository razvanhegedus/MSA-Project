// ─── Enum mirrors ────────────────────────────────────────────────────────────
export type UserRole = 'PLAYER' | 'VENUE_OWNER' | 'ADMIN';
export type SurfaceType = 'SYNTHETIC_3G' | 'INDOOR_TARAFLEX' | 'NATURAL_GRASS' | 'HYBRID';
export type BookingStatus = 'PENDING' | 'CONFIRMED' | 'CANCELLED';
export type MatchType = 'OPEN_LOBBY' | 'SQUAD_CHALLENGE' | 'TOURNAMENT_MATCH';
export type MatchStatus = 'OPEN' | 'FULL' | 'CANCELLED' | 'COMPLETED';
export type TeamSide = 'A' | 'B';
export type ParticipantRole = 'ORGANIZER' | 'PLAYER' | 'GOALKEEPER';
export type ParticipantStatus = 'CONFIRMED' | 'PENDING';
export type TournamentFormat = 'SINGLE_ELIMINATION' | 'GROUP_AND_KNOCKOUT';
export type TournamentStatus = 'REGISTRATION_OPEN' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED';
export type SlotStatus = 'AVAILABLE' | 'OCCUPIED' | 'OPEN_LOBBY' | 'PAST';

// ─── Auth ─────────────────────────────────────────────────────────────────────
export interface RegisterPayload {
  email: string;
  password: string;
  full_name: string;
  phone: string;
  role?: UserRole;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface UserResponse {
  id: string;
  email: string;
  full_name: string;
  phone: string;
  role: UserRole;
  created_at: string;
}

// ─── Venues & Pitches ─────────────────────────────────────────────────────────
export interface VenueResponse {
  id: string;
  owner_id: string;
  name: string;
  address: string;
  city: string;
  phone: string;
  latitude: number;
  longitude: number;
  opening_hour: number;
  closing_hour: number;
  created_at: string;
  pitches?: PitchResponse[];
}

export interface PitchResponse {
  id: string;
  venue_id: string;
  name: string;
  surface_type: SurfaceType;
  team_size_capacity: number;
  hourly_rate: number;
  is_active: boolean;
  venue?: VenueResponse;
}

// ─── Time Slots ───────────────────────────────────────────────────────────────
export interface TimeSlot {
  start_time: string;
  end_time: string;
  status: SlotStatus;
  price: number;
  booking_id?: string | null;
  open_match_id?: string | null;
  spots_left?: number | null;
}

// ─── Bookings ─────────────────────────────────────────────────────────────────
export interface BookingCreatePayload {
  pitch_id: string;
  start_time: string;
  end_time: string;
  create_open_lobby: boolean;
  target_players?: number;
  needed_positions?: string[];
  lobby_description?: string;
}

export interface BookingResponse {
  id: string;
  pitch_id: string;
  booked_by_user_id: string;
  start_time: string;
  end_time: string;
  total_price: number;
  status: BookingStatus;
  created_at: string;
  pitch_name?: string | null;
  venue_name?: string | null;
  city?: string | null;
  match?: MatchDetailResponse | null;
  open_match_id?: string | null;
  target_players?: number | null;
  current_players_count?: number | null;
  spots_left?: number | null;
  needed_positions?: string[] | null;
  lobby_description?: string | null;
}

// ─── Matches ──────────────────────────────────────────────────────────────────
export interface MatchParticipantResponse {
  id: string;
  match_id: string;
  user_id: string;
  team_side: TeamSide;
  role: ParticipantRole;
  status: ParticipantStatus;
  joined_at: string;
}

export interface MatchResponse {
  id: string;
  booking_id: string;
  organizer_id: string;
  tournament_id?: string | null;
  match_type: MatchType;
  target_players: number;
  current_players_count: number;
  needed_positions?: string[] | null;
  description?: string | null;
  status: MatchStatus;
  scheduled_at: string;
  venue_name?: string;
  pitch_name?: string;
  city?: string;
  participants?: MatchParticipantResponse[];
}

export interface MatchDetailResponse extends MatchResponse {
  participants: MatchParticipantResponse[];
}

export interface JoinMatchPayload {
  team_side: TeamSide;
  role: ParticipantRole;
}

export interface MatchUpdatePayload {
  target_players?: number;
  needed_positions?: string[];
  description?: string;
  spots_needed?: number;
}

export interface MatchCreatePayload {
  booking_id: string;
  match_type?: MatchType;
  target_players: number;
  needed_positions?: string[];
  description?: string;
}

// ─── Tournaments ──────────────────────────────────────────────────────────────
export interface TournamentResponse {
  id: string;
  venue_id: string;
  organizer_id: string;
  name: string;
  format: TournamentFormat;
  max_teams: number;
  entry_fee: number;
  start_date: string;
  end_date: string;
  status: TournamentStatus;
  created_at: string;
}

// ─── AI Concierge ─────────────────────────────────────────────────────────────
export interface ToolCallPayload {
  tool_name: string;
  arguments: Record<string, unknown>;
  result_summary: Array<Record<string, unknown>>;
}

export interface AIChatResponse {
  reply: string;
  invoked_tools: ToolCallPayload[];
}

export interface AIChatHistoryMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface AIChatRequest {
  message: string;
  history: AIChatHistoryMessage[];
  default_city?: string;
}

// ─── Pagination ───────────────────────────────────────────────────────────────
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

