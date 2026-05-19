
# -*- coding: utf-8 -*-
"""
DEVIL PICKS — NBA MERGED PROP ENGINE v1.0
NBA only. Streamlit + Railway ready.

Merged ideas:
- Exact Underdog prop-line parsing
- PrizePicks fallback
- Odds API market support
- 10/10 style UI
- MLB v11.17-inspired edge display, hard gates, confidence tiers, CLV snapshots, grading workflow
"""

import os
import re
import json
import math
import difflib
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import requests
import streamlit as st

try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None

APP_VERSION = "NBA MERGED EXACT LINES + 10/10 LIVE TRACKING + v11.17 EDGE LOGIC — RAILWAY SAFE"
APP_TITLE = "DEVIL PICKS — NBA Merged Prop Engine"
SPORT_KEY = "basketball_nba"
CURRENT_SEASON = "2025-26"
DEFAULT_ODDS = -110
MAX_KELLY = 0.03

LOCAL_DIR = "devil_picks_nba_merged"
DRIVE_DIR = "/content/drive/MyDrive/devil_picks_nba_merged"

try:
    from google.colab import drive  # type: ignore
    if not os.path.exists("/content/drive/MyDrive"):
        drive.mount("/content/drive", force_remount=False)
    os.makedirs(DRIVE_DIR, exist_ok=True)
    STORAGE_DIR = DRIVE_DIR
except Exception:
    os.makedirs(LOCAL_DIR, exist_ok=True)
    STORAGE_DIR = LOCAL_DIR

REQUEST_LOG_FILE = os.path.join(STORAGE_DIR, "request_log.json")
PROP_SNAPSHOT_FILE = os.path.join(STORAGE_DIR, "nba_prop_snapshot.json")
MARKET_SNAPSHOT_FILE = os.path.join(STORAGE_DIR, "nba_market_snapshot.json")
EDGE_HISTORY_FILE = os.path.join(STORAGE_DIR, "nba_edge_history.json")
CLOSING_LINE_FILE = os.path.join(STORAGE_DIR, "nba_closing_line_history.json")
GRADED_HISTORY_FILE = os.path.join(STORAGE_DIR, "nba_graded_history.json")
LEARNING_FILE = os.path.join(STORAGE_DIR, "nba_learning.json")
INJURY_LINEUP_FILE = os.path.join(STORAGE_DIR, "nba_injury_lineup_adjustments.json")

NBA_SCOREBOARD = "https://cdn.nba.com/static/json/liveData/scoreboard/scoreboard_00.json"
NBA_TODAY_SCOREBOARD = "https://cdn.nba.com/static/json/liveData/scoreboard/todaysScoreboard_00.json"
ESPN_SCOREBOARD = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
ODDS_BASE = "https://api.the-odds-api.com/v4"
PRIZEPICKS_URL = "https://api.prizepicks.com/projections"
UNDERDOG_URLS = [
    "https://api.underdogfantasy.com/beta/v6/over_under_lines",
    "https://api.underdogfantasy.com/beta/v5/over_under_lines",
    "https://api.underdogfantasy.com/v1/over_under_lines",
]

PROP_CONFIG = {
    "PTS": {"label": "Points", "markets": ["player_points"], "min_edge": 1.8, "limits": (3.5, 45.5), "std": 5.8},
    "REB": {"label": "Rebounds", "markets": ["player_rebounds"], "min_edge": 1.5, "limits": (1.5, 22.5), "std": 3.8},
    "AST": {"label": "Assists", "markets": ["player_assists"], "min_edge": 1.5, "limits": (0.5, 17.5), "std": 3.2},
    "PRA": {"label": "PRA", "markets": ["player_points_rebounds_assists"], "min_edge": 2.5, "limits": (8.5, 65.5), "std": 7.5},
    "PR": {"label": "Points + Rebounds", "markets": ["player_points_rebounds"], "min_edge": 2.2, "limits": (6.5, 58.5), "std": 6.8},
    "PA": {"label": "Points + Assists", "markets": ["player_points_assists"], "min_edge": 2.2, "limits": (6.5, 58.5), "std": 6.6},
    "RA": {"label": "Rebounds + Assists", "markets": ["player_rebounds_assists"], "min_edge": 2.0, "limits": (2.5, 34.5), "std": 5.0},
    "3PM": {"label": "3PM", "markets": ["player_threes"], "min_edge": 0.65, "limits": (0.5, 8.5), "std": 1.7},
}

st.set_page_config(page_title=APP_TITLE, layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
.stApp {background:radial-gradient(circle at top left,#23000a 0%,#07101d 42%,#02040a 100%); color:#fff;}
.block-container {padding-top:1rem; max-width:1650px;}
section[data-testid="stSidebar"] {background:#050912; border-right:1px solid rgba(255,52,79,.25);}
.hero {border:1px solid rgba(255,255,255,.15); background:linear-gradient(135deg,#111827,#070b13); border-radius:24px; padding:22px; box-shadow:0 0 34px rgba(255,52,79,.12); margin-bottom:16px;}
.logo-title {font-size:31px; font-weight:950;}
.sub {color:#aeb7c9; font-size:13px;}
.card {border:1px solid rgba(255,255,255,.14); background:linear-gradient(145deg,#0a111f,#080d18); border-radius:19px; padding:18px; margin-bottom:14px;}
.card-green {border:1px solid rgba(56,240,99,.45); background:linear-gradient(145deg,rgba(0,42,18,.70),rgba(8,13,24,.94)); border-radius:19px; padding:18px; margin-bottom:14px;}
.card-orange {border:1px solid rgba(255,176,46,.45); background:linear-gradient(145deg,rgba(54,32,0,.70),rgba(8,13,24,.94)); border-radius:19px; padding:18px; margin-bottom:14px;}
.card-red {border:1px solid rgba(255,52,79,.45); background:linear-gradient(145deg,rgba(52,5,16,.70),rgba(8,13,24,.94)); border-radius:19px; padding:18px; margin-bottom:14px;}
.metric-grid {display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px; margin:10px 0 16px;}
.metric-box {border:1px solid rgba(255,255,255,.14); background:#0a111f; border-radius:16px; padding:14px; min-height:88px;}
.metric-label {font-size:12px; color:#aeb7c9; text-transform:uppercase; font-weight:800;}
.metric-value {font-size:28px; font-weight:950; margin-top:5px;}
.metric-sub {font-size:12px; color:#aeb7c9; margin-top:4px;}
.team-name {font-size:24px; font-weight:950;}
.green {color:#38f063;} .red {color:#ff344f;} .orange {color:#ffb02e;} .muted {color:#aeb7c9;}
.badge {display:inline-block; padding:7px 12px; border-radius:999px; font-weight:900; font-size:12px; margin:3px 5px 3px 0; border:1px solid rgba(255,255,255,.18); background:#101827; color:#dce4f5;}
.badge-green {background:#002c16; border-color:rgba(56,240,99,.55); color:#b9ffd0;}
.badge-orange {background:#362000; border-color:rgba(255,176,46,.55); color:#ffe1a3;}
.badge-red {background:#3a0711; border-color:rgba(255,52,79,.55); color:#ffd2d8;}
.section-title {font-size:22px; font-weight:950; margin:18px 0 10px; border-left:5px solid #ff344f; padding-left:12px;}
.stTabs [data-baseweb="tab"] {color:#b8c3cf; font-weight:900;}
.stTabs [aria-selected="true"] {color:#ff344f!important; border-bottom:3px solid #ff344f;}
@media (max-width: 1100px) {.metric-grid{grid-template-columns:repeat(2,minmax(0,1fr));}}
</style>
""", unsafe_allow_html=True)

def get_secret(key: str, default: str = "") -> str:
    try:
        value = st.secrets.get(key, default)
        if value:
            return str(value)
    except Exception:
        pass
    return os.getenv(key, default)

ODDS_API_KEY = get_secret("ODDS_API_KEY", "")

def app_now() -> datetime:
    if ZoneInfo:
        return datetime.now(ZoneInfo("America/New_York"))
    return datetime.now(timezone.utc) - timedelta(hours=5)

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def safe_float(x: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        if x is None or x == "":
            return default
        return float(x)
    except Exception:
        return default

def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))

def load_json(path: str, default: Any) -> Any:
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return default

def save_json(path: str, data: Any) -> None:
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp, path)
    except Exception:
        pass

def log_request(source: str, status: str, message: str = "") -> None:
    rows = load_json(REQUEST_LOG_FILE, [])
    rows.append({"time": now_iso(), "source": source[:160], "status": status[:80], "message": str(message)[:500]})
    save_json(REQUEST_LOG_FILE, rows[-700:])

def normalize_name(name: Any) -> str:
    s = str(name or "").lower().strip()
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    return " ".join(s.split())

def name_score(a: Any, b: Any) -> float:
    aa, bb = normalize_name(a), normalize_name(b)
    if not aa or not bb:
        return 0.0
    if aa == bb:
        return 1.0
    if aa in bb or bb in aa:
        return 0.94
    return difflib.SequenceMatcher(None, aa, bb).ratio()

def flatten_json(obj: Any) -> List[Dict[str, Any]]:
    out = []
    if isinstance(obj, dict):
        out.append(obj)
        for v in obj.values():
            out.extend(flatten_json(v))
    elif isinstance(obj, list):
        for v in obj:
            out.extend(flatten_json(v))
    return out

def american_to_decimal(odds: Optional[float]) -> Optional[float]:
    odds = safe_float(odds)
    if odds is None:
        return None
    return 1 + odds / 100 if odds > 0 else 1 + 100 / abs(odds)

def expected_value(prob: Optional[float], odds: Optional[float]) -> Optional[float]:
    dec = american_to_decimal(odds)
    if prob is None or dec is None:
        return None
    return (prob * (dec - 1)) - (1 - prob)

def kelly_fraction(prob: Optional[float], odds: Optional[float]) -> float:
    dec = american_to_decimal(odds)
    if prob is None or dec is None:
        return 0.0
    b = dec - 1
    q = 1 - prob
    if b <= 0:
        return 0.0
    return clamp(((b * prob) - q) / b, 0.0, MAX_KELLY)

def valid_prop_line(prop: str, line: Any) -> bool:
    val = safe_float(line)
    if val is None or prop not in PROP_CONFIG:
        return False
    lo, hi = PROP_CONFIG[prop]["limits"]
    return lo <= val <= hi

def odds_display(o: Optional[float]) -> str:
    o = safe_float(o)
    if o is None:
        return "N/A"
    return f"+{int(o)}" if o > 0 else str(int(o))

def prop_from_market_text(text: Any) -> Optional[str]:
    t = normalize_name(text)
    if any(bad in t for bad in ["wnba", "fantasy score", "turnover", "steals", "blocks", "double double"]):
        return None
    if "points rebounds assists" in t or "pts rebs asts" in t or t == "pra": return "PRA"
    if "points rebounds" in t or "pts rebs" in t: return "PR"
    if "points assists" in t or "pts ast" in t: return "PA"
    if "rebounds assists" in t or "rebs ast" in t: return "RA"
    if any(x in t for x in ["3 pointers", "three pointers", "threes", "3pt", "three point", "3 pm"]): return "3PM"
    if "points" in t or t in ["pts", "point"]: return "PTS"
    if "rebounds" in t or t in ["reb", "rebs"]: return "REB"
    if "assists" in t or t in ["ast", "asts"]: return "AST"
    return None

@st.cache_data(ttl=180, show_spinner=False)
def safe_get_json(url: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None, timeout: int = 7) -> Any:
    h = {
        "User-Agent": "Mozilla/5.0 DevilPicksNBA/1.0",
        "Accept": "application/json,text/plain,*/*",
        "Referer": "https://www.nba.com/",
        "Origin": "https://www.nba.com",
    }
    if headers: h.update(headers)
    try:
        r = requests.get(url, params=params, headers=h, timeout=timeout)
        if r.status_code != 200:
            log_request(url, f"HTTP {r.status_code}", r.text[:250])
            return None
        return r.json()
    except Exception as e:
        log_request(url, "REQUEST_ERROR", str(e))
        return None

def date_for_mode(mode: str) -> str:
    n = app_now()
    if mode == "Tomorrow": n += timedelta(days=1)
    return n.strftime("%Y%m%d")

@st.cache_data(ttl=300, show_spinner=False)
def extract_games(date_yyyymmdd: str) -> List[Dict[str, Any]]:
    games = []
    # ESPN is more reliable than NBA CDN if CDN blocks.
    edata = safe_get_json(ESPN_SCOREBOARD, params={"dates": date_yyyymmdd, "limit": 100})
    if isinstance(edata, dict):
        for ev in edata.get("events", []) or []:
            comps = (ev.get("competitions") or [{}])[0]
            teams = comps.get("competitors", []) or []
            home = next((t for t in teams if t.get("homeAway") == "home"), {})
            away = next((t for t in teams if t.get("homeAway") == "away"), {})
            ht = home.get("team", {}) if isinstance(home, dict) else {}
            at = away.get("team", {}) if isinstance(away, dict) else {}
            games.append({
                "Game ID": ev.get("id"),
                "Date": str(ev.get("date", ""))[:10],
                "Away": at.get("abbreviation"),
                "Home": ht.get("abbreviation"),
                "Away Name": at.get("displayName"),
                "Home Name": ht.get("displayName"),
                "Status": comps.get("status", {}).get("type", {}).get("description"),
                "Source": "ESPN",
            })
    return [g for g in games if g.get("Away") and g.get("Home")]


def get_nested_value(obj: Any, keys: List[str]) -> Any:
    """Find first matching key anywhere inside a nested dict/list."""
    if isinstance(obj, dict):
        for k in keys:
            if k in obj and obj[k] not in [None, ""]:
                return obj[k]
        for v in obj.values():
            found = get_nested_value(v, keys)
            if found not in [None, ""]:
                return found
    elif isinstance(obj, list):
        for v in obj:
            found = get_nested_value(v, keys)
            if found not in [None, ""]:
                return found
    return None

def underdog_text_blob(d: Dict[str, Any]) -> str:
    vals = []
    def walk(x):
        if isinstance(x, dict):
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
        elif isinstance(x, (str, int, float)):
            vals.append(str(x))
    walk(d)
    return " ".join(vals)

def is_probably_nba_text(text: str) -> bool:
    low = f" {text.lower()} "
    bad = [" wnba ", " nfl ", " nhl ", " mlb ", " baseball ", " football ", " soccer ", " tennis ", " golf "]
    if any(x in low for x in bad):
        return False
    good = [" nba ", " basketball ", " points ", " rebounds ", " assists ", " threes ", "3-pointers", "3 pointers"]
    return any(x in low for x in good)

def parse_underdog_props(data: Any, games: List[Dict[str, Any]], selected_props: List[str]) -> List[Dict[str, Any]]:
    """
    Flexible Underdog parser.
    Underdog payloads often nest player/stat/line values differently by endpoint version.
    This parser searches recursively and keeps a diagnostics-friendly Raw field.
    """
    rows = []
    if not data:
        return rows

    dicts = flatten_json(data)
    for d in dicts:
        if not isinstance(d, dict):
            continue

        text = underdog_text_blob(d)
        if not is_probably_nba_text(text):
            continue

        prop = prop_from_market_text(
            get_nested_value(d, [
                "stat_type", "statType", "display_stat", "displayStat",
                "stat", "market", "market_name", "over_under", "overUnder",
                "appearance_stat", "appearanceStat", "title", "description", "name"
            ]) or text
        )
        if prop not in selected_props:
            continue

        # Player name: try relationship/player fields first, then title-ish fields.
        player = get_nested_value(d, [
            "player_name", "playerName", "full_name", "fullName",
            "first_last_name", "firstLastName", "display_name", "displayName",
            "athlete_name", "athleteName"
        ])

        if not player:
            title = get_nested_value(d, ["title", "name", "display_title", "displayTitle", "appearance"])
            if isinstance(title, str):
                # Remove market words if title includes prop text.
                cleaned = re.sub(
                    r"\b(points|rebounds|assists|pts|rebs|asts|pra|threes|3-pointers|over|under)\b",
                    " ",
                    title,
                    flags=re.I,
                )
                cleaned = " ".join(cleaned.split())
                if len(cleaned.split()) >= 2:
                    player = cleaned

        if not player:
            # Last fallback: find a likely capitalized first/last name.
            matches = re.findall(r"\b([A-Z][a-zA-Z.'-]+(?:\s+[A-Z][a-zA-Z.'-]+){1,3})\b", text)
            # Avoid generic words.
            for m in matches:
                ml = m.lower()
                if not any(bad in ml for bad in ["nba", "basketball", "points", "rebounds", "assists", "underdog"]):
                    player = m
                    break

        line = None
        for key in [
            "stat_value", "statValue", "line", "target", "value",
            "over_under_line", "overUnderLine", "line_score", "lineScore",
            "over_under_value", "overUnderValue"
        ]:
            v = get_nested_value(d, [key])
            line = safe_float(v)
            if valid_prop_line(prop, line):
                break
            line = None

        if line is None:
            # Look for realistic half-lines in the text.
            nums = re.findall(r"(?<!\d)(\d{1,2}(?:\.5)?)(?!\d)", text)
            for num in nums:
                val = safe_float(num)
                if valid_prop_line(prop, val):
                    line = val
                    break

        if player and valid_prop_line(prop, line):
            rows.append({
                "Player": str(player).strip(),
                "Prop": prop,
                "Prop Label": PROP_CONFIG[prop]["label"],
                "Line": float(line),
                "Book": "Underdog",
                "Source": "Underdog",
                "Price": None,
                "Raw": text[:350],
            })

    return dedupe_props(rows)

def parse_prizepicks_props(data: Any, selected_props: List[str]) -> List[Dict[str, Any]]:
    rows = []
    if not isinstance(data, dict): return rows
    included = data.get("included", []) or []
    name_by_id = {}
    for x in included:
        if x.get("type") == "new_player":
            name_by_id[str(x.get("id"))] = (x.get("attributes") or {}).get("name")
    for item in data.get("data", []) or []:
        attrs = item.get("attributes") or {}
        text = " ".join(str(v) for v in attrs.values())
        if "NBA" not in text and "basketball" not in text.lower(): 
            continue
        prop = prop_from_market_text(attrs.get("stat_type") or attrs.get("description") or text)
        if prop not in selected_props: continue
        line = safe_float(attrs.get("line_score"))
        rel = ((item.get("relationships") or {}).get("new_player") or {}).get("data") or {}
        player = name_by_id.get(str(rel.get("id"))) or attrs.get("player_name")
        if player and valid_prop_line(prop, line):
            rows.append({
                "Player": player,
                "Prop": prop,
                "Prop Label": PROP_CONFIG[prop]["label"],
                "Line": float(line),
                "Book": "PrizePicks",
                "Source": "PrizePicks",
                "Price": None,
                "Raw": text[:250],
            })
    return dedupe_props(rows)


@st.cache_data(ttl=240, show_spinner=False)
def get_all_live_props(selected_props: List[str]) -> List[Dict[str, Any]]:
    rows = []
    for url in UNDERDOG_URLS:
        data = safe_get_json(url, timeout=7)
        payload_dicts = len(flatten_json(data)) if data is not None else 0
        parsed = parse_underdog_props(data, [], selected_props)
        nba_hint = False
        try:
            blob = underdog_text_blob(data if isinstance(data, dict) else {"data": data})[:200000]
            nba_hint = ("nba" in blob.lower()) or ("basketball" in blob.lower())
        except Exception:
            pass
        status = "OK" if parsed else ("OK_PAYLOAD_HAS_BASKETBALL_BUT_NO_ROWS" if nba_hint else "OK_NO_NBA_HINT")
        log_request(url, status, f"payload_dicts={payload_dicts}; parsed_rows={len(parsed)}; selected={selected_props}")
        rows.extend(parsed)

    pp = safe_get_json(PRIZEPICKS_URL, timeout=7)
    pp_rows = parse_prizepicks_props(pp, selected_props)
    log_request(PRIZEPICKS_URL, "OK" if pp_rows else "OK_NO_ROWS", f"rows={len(pp_rows)}")
    rows.extend(pp_rows)
    return dedupe_props(rows)

def dedupe_props(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    best = {}
    priority = {"Underdog": 0, "PrizePicks": 1, "OddsAPI": 2}
    for r in rows:
        key = (normalize_name(r.get("Player")), r.get("Prop"), safe_float(r.get("Line")))
        if key not in best or priority.get(r.get("Book"), 9) < priority.get(best[key].get("Book"), 9):
            best[key] = r
    return list(best.values())

def parse_manual_adjustments(text: str) -> Dict[str, float]:
    out = {}
    for raw in str(text or "").splitlines():
        line = raw.strip()
        if not line or ":" not in line: continue
        name, val = line.split(":", 1)
        adj = safe_float(val)
        if name.strip() and adj is not None:
            out[normalize_name(name)] = float(adj)
    return out

def get_player_learning(player: str, prop: str) -> float:
    data = load_json(LEARNING_FILE, {})
    return safe_float(data.get(f"{normalize_name(player)}_{prop}"), 0.0) or 0.0

def estimate_projection(row: Dict[str, Any], manual_adjustments: Dict[str, float]) -> Dict[str, Any]:
    """Model projection fallback:
    Uses line as market baseline, then applies small v11.17-style layers:
    - source confidence
    - prop-specific volatility
    - player manual injury/lineup adjustments
    - learned residual from graded history
    This does NOT fake certainty; it creates a stable projection board when no private stats feed is connected.
    """
    line = safe_float(row.get("Line"))
    prop = row.get("Prop")
    if line is None or prop not in PROP_CONFIG:
        return {**row, "Projection": None, "Projection Note": "No valid line"}

    adj = 0.0
    notes = []

    # Source quality
    if row.get("Book") == "Underdog":
        notes.append("Exact Underdog line")
    elif row.get("Book") == "PrizePicks":
        notes.append("PrizePicks fallback")

    # Manual player/team adjustments
    pname = normalize_name(row.get("Player"))
    for key, val in manual_adjustments.items():
        if key and (key in pname or pname in key):
            adj += val
            notes.append(f"Manual adj {val:+.1f}")

    # Learning residual
    learn = get_player_learning(row.get("Player", ""), prop)
    if abs(learn) >= 0.05:
        adj += clamp(learn, -2.5, 2.5)
        notes.append(f"Learning {learn:+.2f}")

    # Conservative default: line is the market center. Small direction comes from manual/learning only.
    projection = float(line + adj)
    return {**row, "Projection": round(projection, 2), "Projection Note": "; ".join(notes) or "Market baseline"}

def normal_over_probability(mean: float, line: float, std: float) -> float:
    # P(X > line), normal approximation.
    z = (line - mean) / max(std, 0.1)
    cdf = 0.5 * (1 + math.erf(z / math.sqrt(2)))
    return clamp(1 - cdf, 0.01, 0.99)

def build_signal(row: Dict[str, Any], default_odds: int, min_edge_extra: float, min_prob: float) -> Dict[str, Any]:
    proj = safe_float(row.get("Projection"))
    line = safe_float(row.get("Line"))
    prop = row.get("Prop")
    if proj is None or line is None or prop not in PROP_CONFIG:
        return {**row, "Pick": "PASS", "Signal": "PASS", "Edge": None, "Pick Prob": None, "EV": None, "Kelly": 0.0, "Reason": "No projection/line"}

    edge = proj - line
    side = "OVER" if edge > 0 else "UNDER"
    abs_edge = abs(edge)
    std = PROP_CONFIG[prop]["std"]
    over_prob = normal_over_probability(proj, line, std)
    pick_prob = over_prob if side == "OVER" else 1 - over_prob
    odds = safe_float(row.get("Price"), default_odds) or default_odds
    ev = expected_value(pick_prob, odds)
    kelly = kelly_fraction(pick_prob, odds)

    base_required = PROP_CONFIG[prop]["min_edge"] + float(min_edge_extra)
    strong_required = base_required * 1.25

    signal = "PASS"
    reason = []
    if abs_edge < base_required:
        reason.append(f"Edge {abs_edge:.2f} below {base_required:.2f}")
    if pick_prob < min_prob:
        reason.append(f"Prob {pick_prob:.1%} below {min_prob:.0%}")
    if ev is not None and ev < -0.03:
        reason.append("Negative EV")

    if not reason:
        signal = "STRONG" if abs_edge >= strong_required and pick_prob >= (min_prob + 0.04) else "LEAN"

    return {
        **row,
        "Pick": side if signal != "PASS" else f"PASS — {side}",
        "Signal": signal,
        "Edge": round(edge, 2),
        "Abs Edge": round(abs_edge, 2),
        "Pick Prob": round(pick_prob, 4),
        "EV": None if ev is None else round(ev, 4),
        "Kelly": round(kelly, 4),
        "Odds Used": int(odds),
        "Reason": "; ".join(reason) if reason else "Passed v11.17-style edge/prob gates",
    }

def make_prop_signals(raw_props: List[Dict[str, Any]], default_odds: int, min_edge: float, min_prob: float, manual_adjustments: Dict[str, float]) -> List[Dict[str, Any]]:
    projected = [estimate_projection(r, manual_adjustments) for r in raw_props]
    signals = [build_signal(r, default_odds, min_edge, min_prob) for r in projected]
    order = {"STRONG": 0, "LEAN": 1, "PASS": 2}
    return sorted(signals, key=lambda r: (order.get(r.get("Signal"), 9), -(r.get("Abs Edge") or 0), -(r.get("Pick Prob") or 0)))

def save_snapshot(path: str, rows: List[Dict[str, Any]]) -> int:
    stamped = [{"snapshot_time": now_iso(), **r} for r in rows]
    save_json(path, stamped)
    return len(stamped)

def append_edge_history(rows: List[Dict[str, Any]]) -> int:
    hist = load_json(EDGE_HISTORY_FILE, [])
    for r in rows:
        if r.get("Line") is not None:
            hist.append({
                "time": now_iso(), "player": r.get("Player"), "prop": r.get("Prop"),
                "book": r.get("Book"), "line": r.get("Line"), "projection": r.get("Projection"),
                "edge": r.get("Edge"), "pick": r.get("Pick"), "signal": r.get("Signal")
            })
    save_json(EDGE_HISTORY_FILE, hist[-5000:])
    return len(rows)

def render_prop_cards(rows: List[Dict[str, Any]], limit: int = 12):
    if not rows:
        st.info("No props loaded yet.")
        return
    for p in rows[:limit]:
        sig = p.get("Signal")
        cls = "card-green" if sig == "STRONG" else "card-orange" if sig == "LEAN" else "card"
        projection = p.get("Projection")
        edge = p.get("Edge")
        prob = p.get("Pick Prob")
        st.markdown(f"""
        <div class='{cls}'>
          <div style='display:flex;justify-content:space-between;gap:14px;align-items:flex-start;flex-wrap:wrap;'>
            <div>
              <div class='team-name'>{p.get('Player')} — {p.get('Prop Label')}</div>
              <div class='sub'>{p.get('Source')} • {p.get('Book')} • Line {p.get('Line')} • {p.get('Projection Note') or ''}</div>
            </div>
            <div style='font-size:27px;font-weight:950;' class='{'green' if sig in ['STRONG','LEAN'] else 'orange'}'>{p.get('Pick')}</div>
          </div>
          <span class='badge {'badge-green' if sig in ['STRONG','LEAN'] else 'badge-orange'}'>{sig}</span>
          <span class='badge'>Proj {'N/A' if projection is None else f'{projection:.2f}'}</span>
          <span class='badge'>Edge {'N/A' if edge is None else f'{edge:+.2f}'}</span>
          <span class='badge'>Prob {'N/A' if prob is None else f'{prob*100:.1f}%'}</span>
          <span class='badge'>EV {'N/A' if p.get('EV') is None else f'{p.get('EV')*100:.1f}%'}</span>
          <span class='badge'>Odds {odds_display(p.get('Odds Used'))}</span>
          <div class='sub' style='margin-top:8px;'>Reason: {p.get('Reason')}</div>
        </div>
        """, unsafe_allow_html=True)

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("### Board Controls")
    day_mode = st.radio("Game Day", ["Today", "Tomorrow", "Both"], index=0)
    selected_props = st.multiselect("NBA props to scan", list(PROP_CONFIG.keys()), default=["PTS", "REB", "AST", "PRA", "3PM"])
    default_odds = st.number_input("Default prop odds when price missing", value=int(DEFAULT_ODDS), step=5)
    min_edge = st.number_input("Extra minimum prop edge", value=0.0, min_value=0.0, step=0.25)
    min_prob = st.slider("Minimum prop probability", 0.50, 0.70, 0.56, 0.01)
    hide_passes = st.checkbox("Hide PASS rows in top pages", value=True)
    show_raw = st.checkbox("Show raw prop table", value=True)
    st.markdown("---")
    st.markdown("### Manual Injury / Lineup Adjustments")
    manual_injury_text = st.text_area(
        "Optional player adjustment",
        value="",
        height=90,
        help="Format: Player Name:+1.5 or Player Name:-2.0. This is the NBA version of lineup/risk adjustment."
    )
    st.caption("Keep manual adjustments small. Use for injury/news context only.")
    st.markdown("---")
    api_override = st.text_input("Odds API key override", value="", type="password")
    if api_override.strip():
        ODDS_API_KEY = api_override.strip()
    st.markdown(f"<span class='badge {'badge-green' if ODDS_API_KEY else 'badge-orange'}'>Odds API: {'KEY SET' if ODDS_API_KEY else 'NO KEY'}</span>", unsafe_allow_html=True)

# ============================================================
# MAIN
# ============================================================
st.markdown(f"""
<div class='hero'>
  <div class='logo-title'>😈 DEVIL PICKS — NBA Merged Prop Engine</div>
  <div class='sub'>{APP_VERSION} • exact lines + 10/10 UI + v11.17-style edge discipline</div>
</div>
""", unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)
refresh = c1.button("🔄 Load / Refresh NBA Board", use_container_width=True)
save_props = c2.button("💾 Save Before Snapshot", use_container_width=True)
save_closing = c3.button("🔒 Save Closing Snapshot", use_container_width=True)
save_edges = c4.button("📈 Save Edge History", use_container_width=True)

if refresh:
    st.cache_data.clear()
    st.session_state["nba_board_loaded"] = True
    st.success("Loading live NBA board...")

# Railway-safe: do not call external APIs during initial health/page load.
# The app renders immediately first, then fetches data only after button click.
if "nba_board_loaded" not in st.session_state:
    st.session_state["nba_board_loaded"] = False

games = []
raw_props = []
prop_signals = []
qualified = []
manual_adjustments = parse_manual_adjustments(manual_injury_text)

if st.session_state.get("nba_board_loaded"):
    dates = [date_for_mode("Today"), date_for_mode("Tomorrow")] if day_mode == "Both" else [date_for_mode(day_mode)]
    for d in dates:
        games.extend(extract_games(d))

    raw_props = get_all_live_props(selected_props)
    prop_signals = make_prop_signals(raw_props, int(default_odds), float(min_edge), float(min_prob), manual_adjustments)
    qualified = [p for p in prop_signals if p.get("Signal") in ["STRONG", "LEAN"]]
else:
    st.info("Railway-safe mode: click **Load / Refresh NBA Board** to fetch games and prop lines.")

if save_props:
    n = save_snapshot(PROP_SNAPSHOT_FILE, prop_signals)
    st.success(f"Saved {n} NBA prop rows to {PROP_SNAPSHOT_FILE}")
if save_closing:
    n = save_snapshot(CLOSING_LINE_FILE, prop_signals)
    st.success(f"Saved {n} NBA closing rows to {CLOSING_LINE_FILE}")
if save_edges:
    n = append_edge_history(prop_signals)
    st.success(f"Saved {n} edge-history rows.")

best_prop = qualified[0] if qualified else (prop_signals[0] if prop_signals else None)
st.markdown(f"""
<div class='metric-grid'>
  <div class='metric-box'><div class='metric-label'>NBA Games Loaded</div><div class='metric-value'>{len(games)}</div><div class='metric-sub'>{day_mode}</div></div>
  <div class='metric-box'><div class='metric-label'>Raw Prop Lines</div><div class='metric-value'>{len(raw_props)}</div><div class='metric-sub'>Underdog / PrizePicks</div></div>
  <div class='metric-box'><div class='metric-label'>Model Plays</div><div class='metric-value'>{len(qualified)}</div><div class='metric-sub'>Passed edge/prob gates</div></div>
  <div class='metric-box'><div class='metric-label'>Best Prop</div><div class='metric-value' style='font-size:19px;'>{(best_prop.get('Player','') + ' ' + best_prop.get('Prop','') + ' ' + best_prop.get('Pick','')) if best_prop else 'No props yet'}</div><div class='metric-sub'>{best_prop.get('Signal','') if best_prop else 'Check diagnostics'}</div></div>
</div>
""", unsafe_allow_html=True)

tab_top, tab_props, tab_raw, tab_games, tab_history, tab_logs = st.tabs([
    "😈 Top Props", "🎯 Prop Signals", "📋 Raw Lines", "🏀 NBA Games", "📈 History", "🔌 Diagnostics"
])

with tab_top:
    st.markdown("<div class='section-title'>Best NBA Player Props</div>", unsafe_allow_html=True)
    show = qualified[:12] if hide_passes else prop_signals[:12]
    if not show:
        st.warning("No qualified props yet. Check Raw Lines and Diagnostics.")
    render_prop_cards(show, 12)

with tab_props:
    st.markdown("<div class='section-title'>All Prop Signals</div>", unsafe_allow_html=True)
    if prop_signals:
        df = pd.DataFrame(prop_signals)
        cols = ["Player", "Prop", "Prop Label", "Projection", "Line", "Edge", "Pick", "Signal", "Pick Prob", "EV", "Kelly", "Book", "Reason"]
        st.dataframe(df[[c for c in cols if c in df.columns]], use_container_width=True, hide_index=True)
    else:
        st.info("No prop signals.")

with tab_raw:
    st.markdown("<div class='section-title'>Raw Prop Lines</div>", unsafe_allow_html=True)
    if raw_props:
        st.dataframe(pd.DataFrame(raw_props), use_container_width=True, hide_index=True)
    else:
        st.warning("No raw NBA prop rows parsed.")

with tab_games:
    st.markdown("<div class='section-title'>NBA Games</div>", unsafe_allow_html=True)
    if games:
        st.dataframe(pd.DataFrame(games), use_container_width=True, hide_index=True)
    else:
        st.info("No games loaded for selected date.")

with tab_history:
    st.markdown("<div class='section-title'>Saved Edge History / Snapshots</div>", unsafe_allow_html=True)
    hist = load_json(EDGE_HISTORY_FILE, [])
    if hist:
        st.dataframe(pd.DataFrame(hist[-300:]), use_container_width=True, hide_index=True)
    else:
        st.info("No edge history saved yet.")

with tab_logs:
    st.markdown("<div class='section-title'>Source Diagnostics</div>", unsafe_allow_html=True)
    logs = load_json(REQUEST_LOG_FILE, [])
    if logs:
        st.dataframe(pd.DataFrame(logs[-300:]), use_container_width=True, hide_index=True)
    else:
        st.info("No request logs yet.")

st.caption("Workflow: refresh board → inspect projection vs line → save before snapshot → save closing snapshot → grade manually after games.")
