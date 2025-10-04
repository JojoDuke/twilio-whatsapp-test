import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None  # type: ignore


RESERVIO_BASE_URL = os.environ.get(
    "RESERVIO_BASE_URL",
    "https://api.reservio.com/v2",
)

# Default business id from user-provided reference
DEFAULT_BUSINESS_ID = os.environ.get(
    "RESERVIO_BUSINESS_ID",
    "ef525423-dabf-4750-bf11-dc5182d68695",
)


def _auth_headers() -> Dict[str, str]:
    api_key = os.environ.get("RESERVIO_API_KEY")
    headers: Dict[str, str] = {"Accept": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


async def get_business_info(business_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    bid = business_id or DEFAULT_BUSINESS_ID
    url = f"{RESERVIO_BASE_URL}/businesses/{bid}"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers=_auth_headers())
            if resp.status_code == 200:
                return resp.json().get("data", {}).get("attributes")
    except Exception:
        pass
    return None


async def get_booking_slots(
    *,
    business_id: Optional[str] = None,
    start_utc: datetime,
    end_utc: datetime,
    service_id: Optional[str] = None,
    resource_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    bid = business_id or DEFAULT_BUSINESS_ID

    params = {
        "filter[from]": start_utc.isoformat(timespec="seconds") + "Z",
        "filter[to]": end_utc.isoformat(timespec="seconds") + "Z",
    }
    if service_id:
        params["filter[serviceId]"] = service_id
    if resource_id:
        params["filter[resourceId]"] = resource_id

    url = f"{RESERVIO_BASE_URL}/businesses/{bid}/availability/booking-slots"
    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            resp = await client.get(url, params=params, headers=_auth_headers())
            if resp.status_code == 200:
                data = resp.json()
                return data.get("data", [])
    except Exception:
        pass
    return []


def summarize_slots(
    slots: List[Dict[str, Any]],
    limit: int = 10,
    timezone: Optional[str] = None,
    min_duration_minutes: Optional[int] = None,
    not_before_utc: Optional[datetime] = None,
    open_hour_local: Optional[int] = None,
    close_hour_local: Optional[int] = None,
    annotate_last_start: bool = False,
) -> str:
    if not slots:
        return "No available booking slots were found in the requested window."

    # Deduplicate by exact start/end to avoid duplicates across resources
    unique: Dict[str, Dict[str, Any]] = {}
    for item in slots:
        attributes = item.get("attributes", {})
        start_iso = attributes.get("start")
        end_iso = attributes.get("end")
        if not start_iso or not end_iso:
            continue
        key = f"{start_iso}|{end_iso}"
        if key not in unique:
            unique[key] = attributes

    # Sort by start time
    def parse_iso(dt_str: str) -> datetime:
        # datetime.fromisoformat supports "+02:00" offsets
        return datetime.fromisoformat(dt_str)

    tzinfo = None
    if timezone:
        try:
            tzinfo = ZoneInfo(timezone) if ZoneInfo is not None else None
        except Exception:
            tzinfo = None

    sorted_items = sorted(unique.values(), key=lambda a: parse_iso(a["start"]))

    lines: List[str] = []
    kept_local_times: List[tuple] = []  # (start_local_dt, end_local_dt)
    for attributes in sorted_items:
        start_dt = parse_iso(attributes["start"])  # aware
        end_dt = parse_iso(attributes["end"])      # aware
        # Skip slots that start before not_before_utc; compare in UTC
        if isinstance(not_before_utc, datetime):
            # Convert both datetimes to UTC using a robust fallback if tzdata is unavailable
            try:
                from datetime import timezone as dt_timezone
                utc = ZoneInfo("UTC") if ZoneInfo is not None else dt_timezone.utc
            except Exception:
                from datetime import timezone as dt_timezone
                utc = dt_timezone.utc

            start_dt_utc = start_dt.astimezone(utc)
            nbu = not_before_utc
            if nbu.tzinfo is None:
                nbu = nbu.replace(tzinfo=utc)
            else:
                nbu = nbu.astimezone(utc)
            if start_dt_utc < nbu:
                continue
        # Filter by minimum duration if provided
        if isinstance(min_duration_minutes, int) and min_duration_minutes > 0:
            total_minutes = int((end_dt - start_dt).total_seconds() // 60)
            if total_minutes < min_duration_minutes:
                continue
        if tzinfo is not None:
            start_dt = start_dt.astimezone(tzinfo)
            end_dt = end_dt.astimezone(tzinfo)
        # Filter by business hours if provided (local time comparisons)
        if isinstance(open_hour_local, int) and isinstance(close_hour_local, int):
            if not (0 <= open_hour_local <= 23 and 0 <= close_hour_local <= 23):
                pass
            else:
                # Require slot fully within [open, close]
                if start_dt.hour < open_hour_local:
                    continue
                if end_dt.hour > close_hour_local or (end_dt.hour == close_hour_local and end_dt.minute > 0):
                    continue
        # Display AM/PM for clarity
        start_str = start_dt.strftime("%I:%M %p").lstrip('0')
        end_str = end_dt.strftime("%I:%M %p").lstrip('0')
        kept_local_times.append((start_dt, end_dt))
        lines.append(f"- {start_str}–{end_str}")
        if len(lines) >= limit:
            break

    if not lines:
        return "Slots data available but could not be parsed."
    if annotate_last_start and kept_local_times:
        last_start = kept_local_times[-1][0]
        # annotate last line
        lines[-1] = lines[-1] + " (last start today)"
    return "Here are some available times (Europe/Prague):\n" + "\n".join(lines)


async def get_services(business_id: Optional[str] = None) -> List[Dict[str, Any]]:
    bid = business_id or DEFAULT_BUSINESS_ID
    url = f"{RESERVIO_BASE_URL}/businesses/{bid}/services"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers=_auth_headers(), params={"page[limit]": 50, "page[offset]": 0})
            if resp.status_code == 200:
                data = resp.json()
                return data.get("data", [])
    except Exception:
        pass
    return []


def summarize_services(services: List[Dict[str, Any]]) -> str:
    if not services:
        return "No services found. Please ask the user to describe the haircut."
    lines: List[str] = ["Available services (reply with the number):"]
    for idx, svc in enumerate(services, start=1):
        attrs = svc.get("attributes", {})
        name = attrs.get("name") or "Unnamed"
        duration = attrs.get("duration") or 0
        duration_min = int(duration // 60) if isinstance(duration, (int, float)) else duration
        lines.append(f"{idx}) {name} — {duration_min} min")
    return "\n".join(lines)


