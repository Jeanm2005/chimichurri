"""
local_data.py

In-memory mock data layer for local development and testing.
Exposes the same function signatures as data_fetcher.py so app.py,
activity_page.py, and community_page.py can swap between real BigQuery
and local mock data by changing a single import.

The recommendation system (VertexAI, future) will consume the same
generate_all() dataset via mock_data_generator.py — this shim just
makes that data available to the Streamlit app without a BigQuery
connection.

Usage in app.py / pages:
    # Development (no BigQuery):
    import local_data as data_fetcher

    # Production (real BigQuery):
    import data_fetcher
"""

import random
from datetime import datetime, timezone
from math import radians, sin, cos, sqrt, atan2

import mock_data_generator as gen

# ---------------------------------------------------------------------------
# Generate + index the full dataset once at import time.
# Streamlit reruns the script on interaction but Python module caching
# means this block only executes once per server process.
# ---------------------------------------------------------------------------

_DATA = gen.generate_all(n_users=20, n_events=40)

# Index tables by their primary key for O(1) lookups
_USERS         = {u["user_id"]:   u for u in _DATA["users"]}
_EVENTS        = {e["event_id"]:  e for e in _DATA["events"]}
_LOCATIONS     = {l["location_id"]: l for l in _DATA["locations"]}

# Pick a stable "current user" that the app will log in as
# (first user in the generated list — deterministic after seeding)
CURRENT_USER_ID = _DATA["users"][0]["user_id"]
CURRENT_USER    = _DATA["users"][0]


# ---------------------------------------------------------------------------
# Haversine distance helper (replaces BigQuery ST_DISTANCE)
# ---------------------------------------------------------------------------

def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Return the great-circle distance in kilometres between two points."""
    R = 6371.0
    dlat = radians(lat2 - lat1)
    dlng = radians(lng2 - lng1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng / 2) ** 2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))


# ---------------------------------------------------------------------------
# USER FUNCTIONS  (mirrors data_fetcher.py)
# ---------------------------------------------------------------------------

def get_user(user_id: str) -> dict | None:
    return _USERS.get(user_id)


def get_users_by_sport(sport: str) -> list[dict]:
    results = []
    for u in _DATA["users"]:
        for s in u.get("sports", []):
            if s["sport"].lower() == sport.lower():
                results.append({
                    "user_id":    u["user_id"],
                    "email":      u["email"],
                    "sport":      s["sport"],
                    "skill_level": s["skill_level"],
                })
    return results


# ---------------------------------------------------------------------------
# FRIENDSHIP FUNCTIONS  (mirrors data_fetcher.py)
# ---------------------------------------------------------------------------

def get_friends(user_id: str) -> list[dict]:
    friends = []
    for row in _DATA["friendships"]:
        if row["user_id"] == user_id and row["status"] == "accepted":
            friend = _USERS.get(row["friend_id"])
            if friend:
                friends.append({
                    "friend_id":  row["friend_id"],
                    "email":      friend["email"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                    # Extras useful for the Messages UI
                    "sports":     friend.get("sports", []),
                })
    return friends


def send_friend_request(user_id: str, friend_id: str) -> None:
    existing = [
        r for r in _DATA["friendships"]
        if (r["user_id"] == user_id and r["friend_id"] == friend_id)
        or (r["user_id"] == friend_id and r["friend_id"] == user_id)
    ]
    if existing:
        raise ValueError(f"Friendship already exists between {user_id} and {friend_id}.")
    now = datetime.now(timezone.utc).isoformat()
    for a, b in [(user_id, friend_id), (friend_id, user_id)]:
        _DATA["friendships"].append({
            "user_id": a, "friend_id": b,
            "status": "pending", "requested_by": user_id,
            "created_at": now, "updated_at": now,
        })


def accept_friend_request(user_id: str, friend_id: str) -> None:
    now = datetime.now(timezone.utc).isoformat()
    for row in _DATA["friendships"]:
        if (row["user_id"] == user_id and row["friend_id"] == friend_id) or \
           (row["user_id"] == friend_id and row["friend_id"] == user_id):
            row["status"] = "accepted"
            row["updated_at"] = now


def reject_friend_request(user_id: str, friend_id: str) -> None:
    _DATA["friendships"] = [
        r for r in _DATA["friendships"]
        if not (
            (r["user_id"] == user_id and r["friend_id"] == friend_id) or
            (r["user_id"] == friend_id and r["friend_id"] == user_id)
        )
    ]


# ---------------------------------------------------------------------------
# EVENT FUNCTIONS  (mirrors data_fetcher.py)
# ---------------------------------------------------------------------------

def get_event(event_id: str) -> dict | None:
    return _EVENTS.get(event_id)


def get_events_by_sport(sport: str, status: str = "open") -> list[dict]:
    now = datetime.now(timezone.utc).isoformat()
    return [
        e for e in _DATA["events"]
        if e["sport"].lower() == sport.lower()
        and e["status"] == status
        and e["visibility"] == "public"
        and e["start_time"] >= now
    ]


def get_nearby_events(
    lat: float,
    lng: float,
    radius_meters: float = 5000,
    status: str = "open",
) -> list[dict]:
    """
    Return public open events within radius_meters of (lat, lng).
    Uses haversine distance instead of BigQuery ST_DISTANCE.
    """
    radius_km = radius_meters / 1000
    now = datetime.now(timezone.utc).isoformat()
    results = []
    for e in _DATA["events"]:
        if e["status"] != status or e["visibility"] != "public":
            continue
        if e["start_time"] < now:
            continue
        loc = e.get("location", {})
        elat, elng = loc.get("lat"), loc.get("lng")
        if elat is None or elng is None:
            continue
        dist_km = _haversine_km(lat, lng, elat, elng)
        if dist_km <= radius_km:
            results.append({**e, "distance_meters": dist_km * 1000})
    results.sort(key=lambda x: x["distance_meters"])
    return results


def get_user_created_events(user_id: str) -> list[dict]:
    return sorted(
        [e for e in _DATA["events"] if e["created_by"] == user_id],
        key=lambda e: e["created_at"],
        reverse=True,
    )


# ---------------------------------------------------------------------------
# EVENT PARTICIPANT FUNCTIONS  (mirrors data_fetcher.py)
# ---------------------------------------------------------------------------

def join_event(user_id: str, event_id: str) -> None:
    event = get_event(event_id)
    if not event:
        raise ValueError(f"Event {event_id} not found.")
    if event["status"] != "open":
        raise ValueError(f"Event {event_id} is not open.")

    # Check already joined
    active = _get_active_participants(event_id)
    if any(p["user_id"] == user_id for p in active):
        raise ValueError(f"User {user_id} already joined event {event_id}.")

    # Check capacity
    if event.get("max_players") and len(active) >= event["max_players"]:
        raise ValueError(f"Event {event_id} is at full capacity.")

    now = datetime.now(timezone.utc).isoformat()
    _DATA["participants"].append({
        "event_id": event_id,
        "user_id":  user_id,
        "joined_at": now,
        "status":   "joined",
    })


def leave_event(user_id: str, event_id: str) -> None:
    now = datetime.now(timezone.utc).isoformat()
    _DATA["participants"].append({
        "event_id":  event_id,
        "user_id":   user_id,
        "joined_at": now,
        "status":    "left",
    })


def _get_active_participants(event_id: str) -> list[dict]:
    """
    Internal: return users whose latest participant row is 'joined'.
    Mirrors the CTE logic in data_fetcher.get_event_participants().
    """
    latest: dict[str, dict] = {}
    for row in _DATA["participants"]:
        if row["event_id"] != event_id:
            continue
        uid = row["user_id"]
        if uid not in latest or row["joined_at"] > latest[uid]["joined_at"]:
            latest[uid] = row
    return [r for r in latest.values() if r["status"] == "joined"]


def get_event_participants(event_id: str) -> list[dict]:
    active = _get_active_participants(event_id)
    result = []
    for row in active:
        user = _USERS.get(row["user_id"], {})
        result.append({
            "user_id":   row["user_id"],
            "email":     user.get("email", ""),
            "joined_at": row["joined_at"],
            "status":    row["status"],
        })
    return sorted(result, key=lambda r: r["joined_at"])


# ---------------------------------------------------------------------------
# ACTIVITY FUNCTIONS  (mirrors data_fetcher.py)
# ---------------------------------------------------------------------------

def log_activity(
    user_id: str,
    activity_type: str,
    event_id: str | None = None,
    sport: str | None = None,
    duration_minutes: int | None = None,
    location: dict | None = None,
) -> None:
    import uuid
    now = datetime.now(timezone.utc).isoformat()
    _DATA["activity"].append({
        "activity_id":      str(uuid.uuid4()),
        "user_id":          user_id,
        "event_id":         event_id,
        "sport":            sport,
        "duration_minutes": duration_minutes,
        "location":         location,
        "activity_type":    activity_type,
        "timestamp":        now,
    })


def get_user_activity(
    user_id: str,
    limit: int = 50,
    activity_type: str | None = None,
) -> list[dict]:
    rows = [
        a for a in _DATA["activity"]
        if a["user_id"] == user_id
        and (activity_type is None or a["activity_type"] == activity_type)
    ]
    rows.sort(key=lambda r: r["timestamp"], reverse=True)
    return rows[:limit]


# ---------------------------------------------------------------------------
# COMMUNITY / POSTS FUNCTIONS  (mirrors data_fetcher.py)
# ---------------------------------------------------------------------------

def get_friend_activity(user_id: str, limit: int = 10) -> list[dict]:
    friend_ids = {r["friend_id"] for r in _DATA["friendships"]
                  if r["user_id"] == user_id and r["status"] == "accepted"}
    rows = [a for a in _DATA["activity"] if a["user_id"] in friend_ids]
    rows.sort(key=lambda r: r["timestamp"], reverse=True)
    result = []
    for row in rows[:limit]:
        user = _USERS.get(row["user_id"], {})
        result.append({**row, "email": user.get("email", "")})
    return result


def create_post(user_id: str, content: str) -> str:
    import uuid
    post_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    _DATA.setdefault("posts", []).append({
        "post_id":    post_id,
        "user_id":    user_id,
        "content":    content,
        "created_at": now,
    })
    return post_id


def get_user_posts(user_id: str, limit: int = 10) -> list[dict]:
    posts = [p for p in _DATA.get("posts", []) if p["user_id"] == user_id]
    posts.sort(key=lambda p: p["created_at"], reverse=True)
    return posts[:limit]


def get_friend_posts(user_id: str, limit: int = 10) -> list[dict]:
    friend_ids = {r["friend_id"] for r in _DATA["friendships"]
                  if r["user_id"] == user_id and r["status"] == "accepted"}
    posts = [p for p in _DATA.get("posts", []) if p["user_id"] in friend_ids]
    posts.sort(key=lambda p: p["created_at"], reverse=True)
    result = []
    for p in posts[:limit]:
        user = _USERS.get(p["user_id"], {})
        result.append({**p, "email": user.get("email", "")})
    return result


# ---------------------------------------------------------------------------
# GENAI ADVICE FUNCTION  (delegates to data_fetcher — same implementation)
# ---------------------------------------------------------------------------

def get_genai_advice(user_id: str) -> str:
    """
    Calls the Anthropic API exactly as data_fetcher.get_genai_advice() does,
    but pulls recent activity from local mock data instead of BigQuery.
    """
    from anthropic import Anthropic
    client = Anthropic()

    recent = get_user_activity(user_id, limit=5)
    if recent:
        sports_played = list({r["sport"] for r in recent if r.get("sport")})
        total_minutes = sum(r["duration_minutes"] or 0 for r in recent)
        context = (
            f"The user has recently played {', '.join(sports_played) if sports_played else 'various sports'} "
            f"for a total of {total_minutes} minutes across their last {len(recent)} sessions."
        )
    else:
        context = "The user is just getting started and has no recent activity yet."

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=200,
        messages=[{
            "role": "user",
            "content": (
                f"{context} "
                "Give them a short (2-3 sentence), friendly tip about joining local sports "
                "events, connecting with friends through sports, or getting more involved in "
                "their sports community. Be specific to their recent activities if possible."
            ),
        }],
    )
    return message.content[0].text


# ---------------------------------------------------------------------------
# RECOMMENDATION FUNCTIONS  (mirrors data_fetcher.py)
# ---------------------------------------------------------------------------

def get_recommended_events(user_id: str, limit: int = 10) -> list[dict]:
    """
    Return precomputed recommendation rows joined with event details.
    When VertexAI is integrated, it will write scored rows into
    _DATA["recommendations"] with the same schema — no other changes needed.
    """
    now = datetime.now(timezone.utc).isoformat()
    results = []
    for r in _DATA["recommendations"]:
        if r["user_id"] != user_id:
            continue
        event = _EVENTS.get(r["event_id"])
        if not event:
            continue
        if event["status"] != "open" or event["visibility"] != "public":
            continue
        if event["start_time"] < now:
            continue
        results.append({
            **event,
            "score":        r["score"],
            "generated_at": r["generated_at"],
        })
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:limit]


# ---------------------------------------------------------------------------
# UI ADAPTER — converts generated events into the shape app.py expects
# ---------------------------------------------------------------------------

def get_events_for_ui(user_origin_lat: float = 25.7617,
                      user_origin_lng: float = -80.1918) -> list[dict]:
    """
    Return all generated events formatted for render_event_card() in app.py.
    This bridges the gap between mock_data_generator's schema and the
    hardcoded MOCK_EVENTS dict that used to live in app.py.

    The VertexAI recommender will score these same event_ids — the UI
    will just sort/filter by score instead of recency.
    """
    sport_emoji = {
        "Soccer": "⚽", "Basketball": "🏀", "Volleyball": "🏐",
        "Tennis": "🎾", "Baseball": "⚾", "Pickleball": "🏓",
    }
    skill_display = {
        "beginner": "Beginner",
        "intermediate": "Intermediate",
        "advanced": "Advanced",
    }

    now = datetime.now(timezone.utc).isoformat()
    ui_events = []

    for e in _DATA["events"]:
        if e["visibility"] != "public":
            continue
        if e["start_time"] < now:
            continue

        loc = e.get("location", {})
        elat = loc.get("lat", user_origin_lat)
        elng = loc.get("lng", user_origin_lng)
        dist_km = round(_haversine_km(user_origin_lat, user_origin_lng, elat, elng), 1)

        # Count current joined participants (latest-status logic)
        active = _get_active_participants(e["event_id"])
        joined_count = len(active)

        # Format times for display
        try:
            st_dt = datetime.fromisoformat(e["start_time"])
            et_dt = datetime.fromisoformat(e["end_time"])
            time_str = st_dt.strftime("%a %b %d · %H:%M") + "–" + et_dt.strftime("%H:%M")
            duration_h = (et_dt - st_dt).total_seconds() / 3600
            duration_str = f"{duration_h:.0f}h" if duration_h == int(duration_h) else f"{duration_h:.1f}h"
        except Exception:
            time_str = e.get("start_time", "")[:16]
            duration_str = "?"

        sport = e.get("sport", "Soccer")
        status_raw = e.get("status", "open")
        # Map generator status values to UI display values
        status_display = "Full" if status_raw == "full" else "Open"

        ui_events.append({
            "id":      e["event_id"],
            "sport":   sport,
            "emoji":   sport_emoji.get(sport, "🏃"),
            "venue":   loc.get("name", "Unknown Venue"),
            "address": loc.get("address", ""),
            "time":    time_str,
            "duration": duration_str,
            "joined":  joined_count,
            "total":   e.get("max_players", 10),
            "skill":   skill_display.get(e.get("skill_level", "intermediate"), "Intermediate"),
            "status":  status_display,
            "dist":    dist_km,
        })

    ui_events.sort(key=lambda x: x["dist"])
    return ui_events


def get_friends_for_ui(user_id: str) -> list[dict]:
    """
    Return friends formatted for the Messages page in app.py.
    Bridges the hardcoded MOCK_FRIENDS list that used to live in app.py.
    """
    sport_emoji = {
        "Soccer": "⚽", "Basketball": "🏀", "Volleyball": "🏐",
        "Tennis": "🎾", "Baseball": "⚾", "Pickleball": "🏓",
    }
    friends = get_friends(user_id)
    result = []
    for f in friends:
        user = _USERS.get(f["friend_id"], {})
        email = user.get("email", "")
        name_part = email.split("@")[0].replace(".", " ").title() if email else f["friend_id"][:8]
        initials = "".join(w[0].upper() for w in name_part.split()[:2])
        sports = user.get("sports", [])
        top_sport = sports[0]["sport"] if sports else "Soccer"
        result.append({
            "name":     name_part,
            "initials": initials,
            "sport":    top_sport,
            "emoji":    sport_emoji.get(top_sport, "🏃"),
            "online":   random.choice([True, False]),  # simulated presence
            "user_id":  f["friend_id"],
        })
    return result