from datetime import date, datetime, time, timedelta, timezone


class BookingTimeError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def _to_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def validate_booking_interval(
    start_time: datetime, end_time: datetime
) -> tuple[datetime, datetime]:
    start = _to_utc(start_time)
    end = _to_utc(end_time)
    duration = end - start

    if duration <= timedelta():
        raise BookingTimeError("INVALID_TIME_RANGE", "end_time must be strictly greater than start_time")
    if duration % timedelta(hours=1):
        raise BookingTimeError("INVALID_TIME_RANGE", "Bookings must be in exact 1-hour increments")
    if duration > timedelta(hours=4):
        raise BookingTimeError("INVALID_TIME_RANGE", "Maximum single booking duration is 4 hours")
    return start, end


def get_venue_booking_window(
    booking_date: date, opening_hour: int, closing_hour: int
) -> tuple[datetime, datetime]:
    midnight = datetime.combine(booking_date, time.min, tzinfo=timezone.utc)
    return midnight + timedelta(hours=opening_hour), midnight + timedelta(hours=closing_hour)


def validate_booking_time(
    start_time: datetime, end_time: datetime, opening_hour: int, closing_hour: int
) -> tuple[datetime, datetime]:
    start, end = validate_booking_interval(start_time, end_time)
    if start <= datetime.now(timezone.utc):
        raise BookingTimeError("PAST", "Cannot book a time slot in the past.")

    opening, closing = get_venue_booking_window(start.date(), opening_hour, closing_hour)
    if start < opening or end > closing:
        raise BookingTimeError(
            "OUTSIDE_OPERATING_HOURS",
            f"Booking outside venue operating hours ({opening_hour}:00 - {closing_hour}:00).",
        )
    return start, end
