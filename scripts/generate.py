#!/usr/bin/env python3
"""Generate FIFA World Cup 2026 .ics calendar files in multiple languages."""

import json
import hashlib
import re
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

from icalendar import Alarm, Calendar, Event, vText

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DATA_URL = "https://raw.githubusercontent.com/openfootball/worldcup.json/master/2026/worldcup.json"
STATE_FILE = Path("data/state.json")
OUTPUT_DIR = Path("calendars")
MATCH_DURATION = timedelta(hours=2)
UID_DOMAIN = "worldcup-calendar"

# ---------------------------------------------------------------------------
# Translations
# ---------------------------------------------------------------------------
LANGUAGES = {
    "en": {
        "calendar_name": "FIFA World Cup 2026",
        "calendar_desc": (
            "All matches of the FIFA World Cup 2026 — "
            "United States, Canada & Mexico"
        ),
        "phase": {
            "Matchday": "Matchday",
            "Round of 32": "Round of 32",
            "Round of 16": "Round of 16",
            "Quarter-final": "Quarter-final",
            "Semi-final": "Semi-final",
            "Match for third place": "Third Place Match",
            "Final": "Final",
        },
        "group": "Group",
        "venue": "Venue",
        "vs": "vs",
        "result": "Result",
        "reminder": "Match starts in 30 minutes",
    },
    "es": {
        "calendar_name": "Copa Mundial de la FIFA 2026",
        "calendar_desc": (
            "Todos los partidos de la Copa Mundial de la FIFA 2026 — "
            "Estados Unidos, Canadá y México"
        ),
        "phase": {
            "Matchday": "Jornada",
            "Round of 32": "Dieciseisavos de Final",
            "Round of 16": "Octavos de Final",
            "Quarter-final": "Cuartos de Final",
            "Semi-final": "Semifinal",
            "Match for third place": "Partido por el Tercer Lugar",
            "Final": "Final",
        },
        "group": "Grupo",
        "venue": "Estadio",
        "vs": "vs",
        "result": "Resultado",
        "reminder": "El partido comienza en 30 minutos",
    },
    "pt": {
        "calendar_name": "Copa do Mundo FIFA 2026",
        "calendar_desc": (
            "Todas as partidas da Copa do Mundo FIFA 2026 — "
            "Estados Unidos, Canadá e México"
        ),
        "phase": {
            "Matchday": "Rodada",
            "Round of 32": "Dezesseis-avos de Final",
            "Round of 16": "Oitavas de Final",
            "Quarter-final": "Quartas de Final",
            "Semi-final": "Semifinal",
            "Match for third place": "Disputa pelo Terceiro Lugar",
            "Final": "Final",
        },
        "group": "Grupo",
        "venue": "Estádio",
        "vs": "x",
        "result": "Resultado",
        "reminder": "A partida começa em 30 minutos",
    },
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def fetch_data(url: str) -> dict:
    """Fetch JSON data from a URL."""
    with urllib.request.urlopen(url, timeout=30) as response:
        return json.load(response)


def parse_utc_offset(tz_str: str):
    """Parse strings like 'UTC-6', 'UTC+5:30' into a timezone."""
    m = re.match(r"UTC([+-])(\d+)(?::(\d+))?", tz_str)
    if not m:
        return timezone.utc
    sign = 1 if m.group(1) == "+" else -1
    hours = int(m.group(2))
    minutes = int(m.group(3)) if m.group(3) else 0
    return timezone(timedelta(hours=sign * hours, minutes=sign * minutes))


def parse_match_datetime(date_str: str, time_str: str) -> datetime:
    """Parse a match date/time into a UTC datetime."""
    parts = time_str.split()
    time_part = parts[0]
    tz = parse_utc_offset(parts[1]) if len(parts) > 1 else timezone.utc
    dt = datetime.strptime(f"{date_str} {time_part}", "%Y-%m-%d %H:%M")
    dt = dt.replace(tzinfo=tz)
    return dt.astimezone(timezone.utc)


def stable_uid(match: dict) -> str:
    """Generate a stable UID for a match based on immutable properties."""
    key = "|".join(
        str(match.get(k, "")) for k in ("date", "time", "round", "ground")
    )
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:12]
    return f"fifa-wc-2026-{digest}@{UID_DOMAIN}"


def localize_phase(phase_key: str, lang: str) -> str:
    """Translate a round/phase name."""
    t = LANGUAGES[lang]["phase"]
    if phase_key.startswith("Matchday "):
        num = phase_key.split(" ", 1)[1]
        return f"{t['Matchday']} {num}"
    return t.get(phase_key, phase_key)


def format_score(match: dict) -> str | None:
    """Extract full-time score if available."""
    score = match.get("score")
    if not score:
        return None
    ft = score.get("ft")
    if ft and len(ft) == 2:
        return f"{ft[0]}-{ft[1]}"
    return None


def event_content_hash(
    summary: str,
    description: str,
    location: str,
    dtstart: datetime,
    dtend: datetime,
    score: str | None,
) -> str:
    """Create a hash of event content to detect changes."""
    payload = "|".join(
        [
            summary,
            description,
            location,
            dtstart.isoformat(),
            dtend.isoformat(),
            score or "",
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# ICS Generation
# ---------------------------------------------------------------------------


def create_event(match: dict, lang: str, state: dict) -> Event:
    """Create an icalendar Event for a single match."""
    t = LANGUAGES[lang]

    uid = stable_uid(match)
    dt_start = parse_match_datetime(match["date"], match["time"])
    dt_end = dt_start + MATCH_DURATION

    team1 = match.get("team1", "TBD")
    team2 = match.get("team2", "TBD")
    phase_key = match.get("round", "")
    phase_localized = localize_phase(phase_key, lang)
    group = match.get("group")
    ground = match.get("ground", "TBD")
    score = format_score(match)

    summary = f"{team1} {t['vs']} {team2}"

    desc_lines = [phase_localized]
    if group:
        desc_lines.append(f"{t['group']}: {group}")
    desc_lines.append(f"{t['venue']}: {ground}")
    if score:
        desc_lines.append(f"{t['result']}: {score}")
    description = "\n".join(desc_lines)

    location = ground

    content_hash = event_content_hash(
        summary, description, location, dt_start, dt_end, score
    )
    prev = state.get(uid, {})
    if prev.get("hash") != content_hash:
        sequence = prev.get("sequence", -1) + 1
        state[uid] = {"sequence": sequence, "hash": content_hash, "score": score}
    else:
        sequence = prev.get("sequence", 0)

    event = Event()
    event.add("uid", uid)
    event.add("dtstamp", datetime.now(timezone.utc))
    event.add("dtstart", dt_start)
    event.add("dtend", dt_end)
    event.add("summary", summary)
    event.add("description", description)
    event.add("location", vText(location))
    event.add("sequence", sequence)
    event.add("status", "CONFIRMED")
    event.add("transp", "OPAQUE")
    event.add("categories", ["FIFA World Cup 2026", "Football"])

    alarm = Alarm()
    alarm.add("action", "DISPLAY")
    alarm.add("description", t["reminder"])
    alarm.add("trigger", timedelta(minutes=-30))
    event.add_component(alarm)

    return event


def generate_calendar(matches: list[dict], lang: str, state: dict) -> Calendar:
    """Generate a complete Calendar for a given language."""
    t = LANGUAGES[lang]

    cal = Calendar()
    cal.add("prodid", f"-//worldcup-calendar//FIFA WC 2026 {lang.upper()}//EN")
    cal.add("version", "2.0")
    cal.add("method", "PUBLISH")
    cal.add("calscale", "GREGORIAN")
    cal.add("x-wr-calname", t["calendar_name"])
    cal.add("x-wr-caldesc", t["calendar_desc"])
    cal.add("x-wr-timezone", "UTC")

    for match in matches:
        event = create_event(match, lang, state)
        cal.add_component(event)

    return cal


# ---------------------------------------------------------------------------
# State persistence (per-language)
# ---------------------------------------------------------------------------


def load_state() -> dict:
    """Load persistent state from disk.

    Returns a dict keyed by language code.
    """
    if STATE_FILE.exists():
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_state(state: dict) -> None:
    """Save persistent state to disk."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Fetching data from {DATA_URL} ...")
    data = fetch_data(DATA_URL)
    matches = data.get("matches", [])
    print(f"Loaded {len(matches)} matches.")

    full_state = load_state()

    for lang in LANGUAGES:
        print(f"Generating {lang}.ics ...")
        lang_state = full_state.get(lang, {})
        cal = generate_calendar(matches, lang, lang_state)
        full_state[lang] = lang_state
        output_path = OUTPUT_DIR / f"{lang}.ics"
        with open(output_path, "wb") as f:
            f.write(cal.to_ical())
        print(f"  Written {output_path}")

    save_state(full_state)
    print("Done.")


if __name__ == "__main__":
    main()
