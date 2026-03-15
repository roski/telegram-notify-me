"""Timezone utilities: IANA data, coordinate lookup and time conversion."""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

# ---------------------------------------------------------------------------
# IANA timezone lists grouped by region for the manual-selection UI
# ---------------------------------------------------------------------------

TIMEZONE_REGIONS: dict[str, list[str]] = {
    "Europe": [
        "Europe/London",
        "Europe/Lisbon",
        "Europe/Madrid",
        "Europe/Paris",
        "Europe/Berlin",
        "Europe/Amsterdam",
        "Europe/Zurich",
        "Europe/Rome",
        "Europe/Copenhagen",
        "Europe/Oslo",
        "Europe/Stockholm",
        "Europe/Helsinki",
        "Europe/Prague",
        "Europe/Budapest",
        "Europe/Warsaw",
        "Europe/Kyiv",
        "Europe/Bucharest",
        "Europe/Sofia",
        "Europe/Belgrade",
        "Europe/Zagreb",
        "Europe/Athens",
        "Europe/Istanbul",
    ],
    "America": [
        "America/New_York",
        "America/Toronto",
        "America/Chicago",
        "America/Denver",
        "America/Los_Angeles",
        "America/Vancouver",
        "America/Halifax",
        "America/Anchorage",
        "America/Mexico_City",
        "America/Bogota",
        "America/Lima",
        "America/Caracas",
        "America/Sao_Paulo",
        "America/Buenos_Aires",
    ],
    "Asia": [
        "Asia/Dubai",
        "Asia/Riyadh",
        "Asia/Tehran",
        "Asia/Karachi",
        "Asia/Tashkent",
        "Asia/Almaty",
        "Asia/Dhaka",
        "Asia/Kolkata",
        "Asia/Bangkok",
        "Asia/Jakarta",
        "Asia/Ho_Chi_Minh",
        "Asia/Singapore",
        "Asia/Shanghai",
        "Asia/Taipei",
        "Asia/Seoul",
        "Asia/Tokyo",
        "Asia/Manila",
        "Asia/Vladivostok",
    ],
    "Africa": [
        "Africa/Dakar",
        "Africa/Accra",
        "Africa/Lagos",
        "Africa/Algiers",
        "Africa/Tunis",
        "Africa/Tripoli",
        "Africa/Cairo",
        "Africa/Khartoum",
        "Africa/Nairobi",
        "Africa/Addis_Ababa",
        "Africa/Johannesburg",
        "Africa/Casablanca",
    ],
    "Oceania": [
        "Australia/Perth",
        "Australia/Brisbane",
        "Australia/Sydney",
        "Australia/Melbourne",
        "Pacific/Auckland",
        "Pacific/Fiji",
        "Pacific/Noumea",
        "Pacific/Honolulu",
    ],
    "UTC": [
        "UTC",
    ],
}

# Ordered list of regions shown in the selection menu
REGION_ORDER: list[str] = list(TIMEZONE_REGIONS.keys())


def tz_display_name(iana_tz: str) -> str:
    """Return a short city/zone name for display (e.g. 'Europe/Kyiv' → 'Kyiv')."""
    return iana_tz.rsplit("/", 1)[-1].replace("_", " ")


def timezone_from_location(latitude: float, longitude: float) -> str | None:
    """Return the IANA timezone string for the given GPS coordinates, or None."""
    try:
        from timezonefinder import TimezoneFinder

        tf = TimezoneFinder()
        return tf.timezone_at(lat=latitude, lng=longitude)
    except Exception:
        return None


def is_valid_timezone(tz_str: str) -> bool:
    """Return True if tz_str is a valid IANA timezone."""
    try:
        ZoneInfo(tz_str)
        return True
    except (ZoneInfoNotFoundError, KeyError):
        return False


def user_to_utc(naive_dt: datetime, tz_str: str) -> datetime:
    """Convert a *naive* datetime expressed in the user's timezone to UTC.

    Returns an *aware* datetime in UTC.
    """
    try:
        local_tz = ZoneInfo(tz_str)
    except (ZoneInfoNotFoundError, KeyError):
        local_tz = ZoneInfo("UTC")
    local_dt = naive_dt.replace(tzinfo=local_tz)
    return local_dt.astimezone(ZoneInfo("UTC"))


def utc_to_user(aware_utc_dt: datetime, tz_str: str) -> datetime:
    """Convert an *aware* UTC datetime to the user's local timezone.

    Returns an *aware* datetime in the user's timezone.
    """
    try:
        local_tz = ZoneInfo(tz_str)
    except (ZoneInfoNotFoundError, KeyError):
        local_tz = ZoneInfo("UTC")
    return aware_utc_dt.astimezone(local_tz)
