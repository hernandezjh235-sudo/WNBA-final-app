
# -*- coding: utf-8 -*-
import os, re, json, math, difflib, unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import requests
import streamlit as st

APP_VERSION = "WNBA ODDSAPI CLEAN v1.8 TAB FIX"
DEFAULT_ODDS_API_KEY = "c9f5eadbe263f64c3fd17df20a4f1f3b"

SPORT_KEY = "basketball_wnba"
ODDS_API_BASE = "https://api.the-odds-api.com/v4"
ODDS_FORMAT = "american"

MARKET_MAP = {
    "player_points": "Points",
    "player_rebounds": "Rebounds",
    "player_assists": "Assists",
    "player_threes": "3PT Made",
    "player_steals": "Steals",
    "player_blocks": "Blocks",
    "player_points_rebounds_assists": "Pts + Rebs + Asts",
    "player_points_rebounds": "Pts + Rebs",
    "player_points_assists": "Pts + Asts",
    "player_rebounds_assists": "Rebs + Asts",
}

MARKET_STD = {
    "player_points": 5.5,
    "player_rebounds": 3.2,
    "player_assists": 2.8,
    "player_threes": 1.55,
    "player_steals": 1.05,
    "player_blocks": 0.95,
    "player_points_rebounds_assists": 7.4,
    "player_points_rebounds": 6.6,
    "player_points_assists": 6.4,
    "player_rebounds_assists": 4.4,
}

# Projection baselines only. Lines always come from The Odds API.
DEFAULT_PROJECTION_DB = {
    "Aja Wilson": {"points": 27.5, "rebounds": 11.8, "assists": 2.4, "threes": 0.7, "steals": 1.7, "blocks": 2.4, "pace": 1.01, "dvp": 1.00},
    "Breanna Stewart": {"points": 20.4, "rebounds": 8.5, "assists": 3.6, "threes": 1.7, "steals": 1.6, "blocks": 1.3, "pace": 1.00, "dvp": 1.00},
    "Sabrina Ionescu": {"points": 18.2, "rebounds": 4.8, "assists": 6.0, "threes": 2.8, "steals": 1.0, "blocks": 0.3, "pace": 1.00, "dvp": 1.00},
    "Caitlin Clark": {"points": 19.2, "rebounds": 5.7, "assists": 8.4, "threes": 3.1, "steals": 1.3, "blocks": 0.7, "pace": 1.02, "dvp": 1.00},
    "Napheesa Collier": {"points": 21.5, "rebounds": 9.2, "assists": 3.4, "threes": 1.1, "steals": 1.8, "blocks": 1.4, "pace": 1.00, "dvp": 1.00},
    "Alyssa Thomas": {"points": 11.0, "rebounds": 8.5, "assists": 7.8, "threes": 0.0, "steals": 1.6, "blocks": 0.5, "pace": 0.99, "dvp": 1.00},
    "Angel Reese": {"points": 13.6, "rebounds": 13.1, "assists": 1.9, "threes": 0.1, "steals": 1.3, "blocks": 0.5, "pace": 1.00, "dvp": 1.00},
    "Arike Ogunbowale": {"points": 22.2, "rebounds": 4.5, "assists": 5.1, "threes": 2.8, "steals": 2.0, "blocks": 0.2, "pace": 1.01, "dvp": 1.00},
    "Kelsey Plum": {"points": 18.5, "rebounds": 2.5, "assists": 4.7, "threes": 2.4, "steals": 1.0, "blocks": 0.1, "pace": 1.01, "dvp": 1.00},
    "Jackie Young": {"points": 16.9, "rebounds": 4.4, "assists": 5.1, "threes": 1.8, "steals": 1.2, "blocks": 0.4, "pace": 1.01, "dvp": 1.00},
    "Chelsea Gray": {"points": 12.8, "rebounds": 3.1, "assists": 5.5, "threes": 1.4, "steals": 1.0, "blocks": 0.5, "pace": 1.00, "dvp": 1.00},
    "Kelsey Mitchell": {"points": 19.0, "rebounds": 2.2, "assists": 2.4, "threes": 2.6, "steals": 0.8, "blocks": 0.2, "pace": 1.01, "dvp": 1.00},
    "Aliyah Boston": {"points": 14.0, "rebounds": 8.6, "assists": 3.2, "threes": 0.2, "steals": 0.9, "blocks": 1.2, "pace": 1.00, "dvp": 1.00},
    "Jewell Loyd": {"points": 19.7, "rebounds": 4.4, "assists": 3.4, "threes": 2.1, "steals": 1.4, "blocks": 0.2, "pace": 1.00, "dvp": 1.00},
    "Nneka Ogwumike": {"points": 16.5, "rebounds": 7.4, "assists": 2.3, "threes": 0.6, "steals": 1.7, "blocks": 0.5, "pace": 1.00, "dvp": 1.00},
    "Kahleah Copper": {"points": 18.7, "rebounds": 4.3, "assists": 2.3, "threes": 1.6, "steals": 0.9, "blocks": 0.2, "pace": 1.01, "dvp": 1.00},
    "Rhyne Howard": {"points": 17.5, "rebounds": 4.9, "assists": 3.4, "threes": 2.7, "steals": 1.6, "blocks": 0.6, "pace": 1.00, "dvp": 1.00},
    "Allisha Gray": {"points": 15.6, "rebounds": 4.0, "assists": 2.5, "threes": 1.8, "steals": 1.0, "blocks": 0.5, "pace": 1.00, "dvp": 1.00},
    "Dearica Hamby": {"points": 16.8, "rebounds": 9.3, "assists": 3.4, "threes": 0.9, "steals": 1.5, "blocks": 0.2, "pace": 1.00, "dvp": 1.00},
    "Rickea Jackson": {"points": 13.4, "rebounds": 3.9, "assists": 1.5, "threes": 1.0, "steals": 0.6, "blocks": 0.2, "pace": 1.00, "dvp": 1.00},
    "Jonquel Jones": {"points": 14.5, "rebounds": 9.0, "assists": 2.5, "threes": 1.2, "steals": 0.8, "blocks": 1.1, "pace": 1.00, "dvp": 1.00},
    "Brittney Griner": {"points": 17.8, "rebounds": 6.6, "assists": 2.3, "threes": 0.0, "steals": 0.5, "blocks": 1.5, "pace": 1.00, "dvp": 1.00},
    "Satou Sabally": {"points": 18.6, "rebounds": 8.1, "assists": 4.4, "threes": 1.8, "steals": 1.3, "blocks": 0.5, "pace": 1.00, "dvp": 1.00},
    "Skylar Diggins": {"points": 15.1, "rebounds": 2.8, "assists": 6.2, "threes": 1.2, "steals": 1.3, "blocks": 0.4, "pace": 1.00, "dvp": 1.00},
    "Marina Mabrey": {"points": 14.5, "rebounds": 4.4, "assists": 4.1, "threes": 2.1, "steals": 1.2, "blocks": 0.3, "pace": 1.00, "dvp": 1.00},
    "Brionna Jones": {"points": 13.4, "rebounds": 5.5, "assists": 1.8, "threes": 0.0, "steals": 1.1, "blocks": 0.6, "pace": 0.99, "dvp": 1.00},
    "Paige Bueckers": {"points": 14.0, "rebounds": 4.0, "assists": 4.5, "threes": 1.5, "steals": 1.1, "blocks": 0.3, "pace": 1.00, "dvp": 1.00},
}

NBA_BLOCKLIST = {
    "victor wembanyama", "donovan mitchell", "lebron james", "luka doncic",
    "nikola jokic", "shai gilgeous alexander", "stephen curry", "jayson tatum",
    "jaylen brown", "kevin durant", "devin booker", "kyrie irving",
    "giannis antetokounmpo", "joel embiid", "anthony edwards", "jalen brunson",
    "tyrese haliburton", "ja morant", "trae young", "james harden",
}

STORAGE_DIR = os.getenv("STORAGE_DIR", "wnba_oddsapi_engine")
Path(STORAGE_DIR).mkdir(parents=True, exist_ok=True)

PICK_LOG = os.path.join(STORAGE_DIR, "official_pick_log.json")
RESULT_LOG = os.path.join(STORAGE_DIR, "graded_result_log.json")
LEARN_FILE = os.path.join(STORAGE_DIR, "player_learning.json")
CLV_FILE = os.path.join(STORAGE_DIR, "clv_tracker.json")
LINE_HISTORY_FILE = os.path.join(STORAGE_DIR, "line_history.json")
REQUEST_LOG_FILE = os.path.join(STORAGE_DIR, "request_log.json")
BEFORE_AFTER_FILE = os.path.join(STORAGE_DIR, "before_after_snapshots.json")
CUSTOM_STATS_FILE = os.path.join(STORAGE_DIR, "custom_projection_stats.json")
MANUAL_LINES_FILE = os.path.join(STORAGE_DIR, "manual_line_overrides.json")
MANUAL_PROPS_FILE = os.path.join(STORAGE_DIR, "manual_prop_board.json")

st.set_page_config(page_title="WNBA Prop Engine", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
.stApp {background:radial-gradient(circle at top left,#141827 0%,#07090f 42%,#020204 100%);color:#fff;}
.block-container {padding-top:1.0rem;max-width:1680px;}
.hero-panel {background:linear-gradient(135deg,rgba(30,38,72,.96),rgba(8,10,18,.98));border:1px solid rgba(128,162,255,.38);border-radius:26px;padding:22px;box-shadow:0 0 32px rgba(80,120,255,.16);margin-bottom:18px;}
.big-title {font-size:42px;font-weight:950;letter-spacing:-1px;}
.sub-title {color:#c7cfdf;font-size:15px;margin-top:-6px;}
.small-muted {color:#aeb6c8;font-size:13px;}
.clean-card {background:linear-gradient(145deg,#10131d,#090b12);border:1px solid rgba(145,170,255,.22);border-radius:20px;padding:18px;box-shadow:0 0 18px rgba(80,120,255,.08);margin-bottom:14px;}
.green-card {background:linear-gradient(145deg,#061c13,#07100c);border:1px solid rgba(0,255,145,.34);border-radius:20px;padding:18px;box-shadow:0 0 20px rgba(0,255,145,.13);margin-bottom:14px;}
.warn-card {background:linear-gradient(145deg,#211600,#100b02);border:1px solid rgba(255,195,70,.34);border-radius:20px;padding:18px;box-shadow:0 0 18px rgba(255,195,70,.10);margin-bottom:14px;}
.red-card {background:linear-gradient(145deg,#240808,#100404);border:1px solid rgba(255,90,90,.34);border-radius:20px;padding:18px;box-shadow:0 0 18px rgba(255,90,90,.10);margin-bottom:14px;}
.game-card {background:linear-gradient(145deg,#12182a,#080a12);border:1px solid rgba(145,170,255,.28);border-radius:18px;padding:14px;margin-bottom:10px;}
.badge {display:inline-block;padding:6px 11px;border-radius:999px;background:#141827;border:1px solid rgba(160,180,255,.38);color:#dce5ff;font-weight:850;margin:3px 4px 3px 0;}
.good-badge {background:#002818;border-color:rgba(0,255,145,.48);color:#b9ffdc;}
.yellow-badge {background:#2a1e00;border-color:rgba(255,210,70,.48);color:#ffe6a6;}
.red-badge {background:#2a0707;border-color:rgba(255,90,90,.48);color:#ffc4c4;}
.blue-badge {background:#111d38;border-color:rgba(128,162,255,.48);color:#dce5ff;}
.kpi-strip {display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:12px;margin:12px 0 18px 0;}
.kpi-box {background:linear-gradient(145deg,#10131d,#080a10);border:1px solid rgba(145,170,255,.24);border-radius:18px;padding:14px;min-height:92px;}
.kpi-label {font-size:12px;color:#aeb6c8;font-weight:850;letter-spacing:.04em;text-transform:uppercase;}
.kpi-value {font-size:25px;font-weight:950;color:#fff;margin-top:6px;}
.kpi-sub {font-size:12px;color:#c7cfdf;margin-top:5px;}
.stTabs [data-baseweb="tab"] {color:#b8c3cf;font-weight:850;}
.stTabs [aria-selected="true"] {color:#8db3ff!important;border-bottom:3px solid #8db3ff;}
[data-testid="stMetric"] {background:linear-gradient(145deg,#10131d,#080a10);border:1px solid rgba(145,170,255,.24);border-radius:18px;padding:13px;}
@media (max-width:1100px){.kpi-strip{grid-template-columns:repeat(2,minmax(0,1fr));}}
</style>
""", unsafe_allow_html=True)

def now_iso(): return datetime.now().isoformat(timespec="seconds")
def today_str(): return datetime.now().strftime("%Y-%m-%d")
def tomorrow_str(): return (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

def safe_float(x, default=None):
    try:
        if x is None or x == "": return default
        return float(x)
    except Exception:
        return default

def safe_int(x, default=None):
    try:
        if x is None or x == "": return default
        return int(float(x))
    except Exception:
        return default

def clamp(x, lo, hi): return max(lo, min(hi, x))

def load_json(path, default):
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return default

def save_json(path, data):
    try:
        Path(os.path.dirname(path)).mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass

def log_source_request(source, status, message=""):
    rows = load_json(REQUEST_LOG_FILE, [])
    rows.append({"time": now_iso(), "source": str(source)[:220], "status": str(status)[:80], "message": str(message)[:800]})
    save_json(REQUEST_LOG_FILE, rows[-700:])

def strip_accents(text):
    try:
        return "".join(ch for ch in unicodedata.normalize("NFKD", str(text or "")) if not unicodedata.combining(ch))
    except Exception:
        return str(text or "")

def normalize_name(name):
    s = strip_accents(name).lower().strip()
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    for suffix in [" jr", " sr", " ii", " iii", " iv"]:
        s = s.replace(suffix, " ")
    return " ".join(s.split())

def name_score(a, b):
    a_norm, b_norm = normalize_name(a), normalize_name(b)
    if not a_norm or not b_norm: return 0.0
    if a_norm == b_norm: return 1.0
    if a_norm in b_norm or b_norm in a_norm: return 0.94
    ap, bp = a_norm.split(), b_norm.split()
    if ap and bp and ap[-1] == bp[-1] and ap[0][:1] == bp[0][:1]: return 0.93
    return difflib.SequenceMatcher(None, a_norm, b_norm).ratio()

def get_api_key():
    # Avoid st.secrets because Streamlit prints "No secrets found" when no secrets.toml exists.
    # Railway/Streamlit environment variable can still override the default key.
    return os.getenv("ODDS_API_KEY", DEFAULT_ODDS_API_KEY)

def safe_get_json(url, params=None, timeout=20):
    try:
        r = requests.get(url, params=params, timeout=timeout, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
        if r.status_code != 200:
            log_source_request(url, f"HTTP {r.status_code}", r.text[:800])
            return None
        return r.json()
    except Exception as e:
        log_source_request(url, "REQUEST_ERROR", str(e))
        return None

def is_nba_leak(name):
    n = normalize_name(name)
    if n in NBA_BLOCKLIST: return True
    return any(tok in n for tok in ["wembanyama", "jokic", "doncic", "gilgeous", "antetokounmpo", "mitchell"])

def is_bad_player_name(name):
    low = str(name or "").lower()
    if not low.strip(): return True
    if is_nba_leak(low): return True
    if any(x in low for x in ["dota", "gaming", "esports", "natus", "vincere", "counter-strike", "cs2", "valorant", "league of legends", " vs ", " vs. ", " @ "]): return True
    if ":" in str(name) or len(str(name).split()) > 5 or len(str(name).split()) < 2: return True
    return False

def american_to_decimal(odds):
    odds = safe_float(odds)
    if odds is None: return None
    return 1 + odds / 100 if odds > 0 else 1 + 100 / abs(odds)

def expected_value(prob, odds=-110):
    dec = american_to_decimal(odds)
    if prob is None or dec is None: return None
    return (prob * (dec - 1)) - (1 - prob)

def kelly_fraction(prob, odds=-110):
    dec = american_to_decimal(odds)
    if prob is None or dec is None: return 0.0
    b = dec - 1
    q = 1 - prob
    if b <= 0: return 0.0
    return float(clamp(((b * prob) - q) / b, 0, 0.25))

def normal_side_probability(proj, line, std, side):
    std = max(safe_float(std, 1.0) or 1.0, 0.35)
    z = (line - proj) / std
    cdf = 0.5 * (1 + math.erf(z / math.sqrt(2)))
    return float(clamp(1 - cdf if side == "OVER" else cdf, 0.001, 0.999))

def utc_to_local_day_label(iso_time):
    try:
        dt = datetime.fromisoformat(str(iso_time).replace("Z", "+00:00"))
        local_date = dt.astimezone().date().isoformat()
        if local_date == today_str(): return "Today"
        if local_date == tomorrow_str(): return "Tomorrow"
        return local_date
    except Exception:
        return "Unknown"

@st.cache_data(ttl=180, show_spinner=False)
def fetch_wnba_events(api_key, days_ahead=2):
    if not api_key: return []
    url = f"{ODDS_API_BASE}/sports/{SPORT_KEY}/events"
    data = safe_get_json(url, params={"apiKey": api_key}, timeout=15)
    if not isinstance(data, list): return []
    out = []
    now = datetime.now(timezone.utc)
    max_dt = now + timedelta(days=days_ahead + 1)
    for g in data:
        try:
            ct = datetime.fromisoformat(str(g.get("commence_time")).replace("Z", "+00:00"))
            if ct <= max_dt: out.append(g)
        except Exception:
            out.append(g)
    log_source_request("The Odds API events", "OK", f"{len(out)} WNBA events loaded")
    return out

@st.cache_data(ttl=180, show_spinner=False)
def fetch_event_player_props(api_key, event_id, markets, regions, bookmakers=""):
    if not api_key or not event_id: return None
    url = f"{ODDS_API_BASE}/sports/{SPORT_KEY}/events/{event_id}/odds"
    params = {"apiKey": api_key, "regions": regions, "markets": markets, "oddsFormat": ODDS_FORMAT}
    if bookmakers.strip(): params["bookmakers"] = bookmakers.strip()
    data = safe_get_json(url, params=params, timeout=20)
    if isinstance(data, dict):
        log_source_request(f"The Odds API event odds {event_id}", "OK", f"bookmakers={len(data.get('bookmakers', []))}")
        return data
    return None

def clean_player_from_outcome(outcome):
    name = outcome.get("description") or outcome.get("player_name") or outcome.get("participant") or ""
    name = str(name).strip()
    if not name or is_bad_player_name(name): return None
    return name

def parse_event_props(event_odds):
    rows = []
    if not isinstance(event_odds, dict): return rows
    event_id = event_odds.get("id")
    sport_key = event_odds.get("sport_key")
    sport_title = event_odds.get("sport_title", "")
    if sport_key != SPORT_KEY and "WNBA" not in str(sport_title).upper(): return rows
    home_team = event_odds.get("home_team", "")
    away_team = event_odds.get("away_team", "")
    commence_time = event_odds.get("commence_time", "")
    matchup = f"{away_team} @ {home_team}".strip(" @")

    for book in event_odds.get("bookmakers", []) or []:
        book_title = book.get("title") or book.get("key") or "Unknown Book"
        book_key = book.get("key") or book_title
        for market in book.get("markets", []) or []:
            market_key = market.get("key")
            if market_key not in MARKET_MAP: continue
            for outcome in market.get("outcomes", []) or []:
                side_raw = str(outcome.get("name", "")).strip().upper()
                if side_raw not in ["OVER", "UNDER"]: continue
                player = clean_player_from_outcome(outcome)
                line = safe_float(outcome.get("point"))
                price = safe_float(outcome.get("price"), -110)
                if not player or line is None: continue
                if line < 0 or line > 100: continue
                rows.append({
                    "Event ID": event_id, "Game Day": utc_to_local_day_label(commence_time),
                    "Commence Time": commence_time, "Matchup": matchup, "Home Team": home_team,
                    "Away Team": away_team, "Book": book_title, "Book Key": book_key,
                    "Market": market_key, "Market Label": MARKET_MAP[market_key],
                    "Player": player, "Side Offered": side_raw, "Line": float(line),
                    "Price": price, "Source": "The Odds API", "Real Line": True,
                })
    return rows

def merge_over_under_rows(rows):
    grouped = {}
    for r in rows:
        key = (normalize_name(r["Player"]), r["Market"], r["Book"], float(r["Line"]), r["Event ID"])
        base = grouped.setdefault(key, {**r, "Over Price": None, "Under Price": None})
        if r["Side Offered"] == "OVER": base["Over Price"] = r["Price"]
        elif r["Side Offered"] == "UNDER": base["Under Price"] = r["Price"]
    out = []
    for item in grouped.values():
        item.pop("Side Offered", None)
        item["Book Count"] = 1
        out.append(item)
    return out

def consensus_lines(rows):
    grouped = {}
    for r in rows:
        key = (normalize_name(r["Player"]), r["Market"], r["Event ID"])
        grouped.setdefault(key, []).append(r)
    out = []
    for _, group in grouped.items():
        lines = [safe_float(g.get("Line")) for g in group if safe_float(g.get("Line")) is not None]
        books = sorted(set(str(g.get("Book")) for g in group))
        consensus = float(np.median(lines)) if lines else None
        for g in group:
            rr = dict(g)
            rr["Consensus Line"] = consensus
            rr["Book Count"] = len(books)
            rr["Books"] = ", ".join(books[:8]) + ("..." if len(books) > 8 else "")
            rr["Alt Line"] = consensus is not None and abs(float(rr["Line"]) - consensus) >= 1.0
            out.append(rr)
    return out


def load_manual_props():
    data = load_json(MANUAL_PROPS_FILE, [])
    return data if isinstance(data, list) else []

def save_manual_props(rows):
    save_json(MANUAL_PROPS_FILE, rows)

def add_manual_prop(player, market, line, book="Manual/Underdog", matchup="Manual Entry", game_day="Manual", over_price=-110, under_price=-110, note=""):
    rows = load_manual_props()
    rec = {
        "id": f"{now_iso()}::{normalize_name(player)}::{market}::{line}",
        "Event ID": "manual",
        "Game Day": game_day or "Manual",
        "Commence Time": "",
        "Matchup": matchup or "Manual Entry",
        "Home Team": "",
        "Away Team": "",
        "Book": book or "Manual/Underdog",
        "Book Key": "manual",
        "Market": market,
        "Market Label": MARKET_MAP.get(market, market),
        "Player": player.strip(),
        "Line": float(line),
        "Price": -110,
        "Over Price": safe_float(over_price, -110) or -110,
        "Under Price": safe_float(under_price, -110) or -110,
        "Source": "Manual Line",
        "Real Line": True,
        "Book Count": 1,
        "Consensus Line": float(line),
        "Books": book or "Manual/Underdog",
        "Alt Line": False,
        "Manual Prop": True,
        "Manual Note": note,
        "Created At": now_iso(),
    }
    rows.append(rec)
    save_manual_props(rows[-500:])
    return rec

def clear_manual_props():
    save_manual_props([])
    return True

def delete_manual_prop(row_id):
    rows = load_manual_props()
    new_rows = [r for r in rows if r.get("id") != row_id]
    save_manual_props(new_rows)
    return len(rows) - len(new_rows)


def fetch_all_real_props(api_key, selected_markets, regions, bookmakers, days_ahead):
    events = fetch_wnba_events(api_key, days_ahead=days_ahead)
    if not selected_markets:
        return [], events
    market_query = ",".join(selected_markets)
    all_rows = []
    for ev in events:
        eid = ev.get("id")
        if not eid: continue
        data = fetch_event_player_props(api_key, eid, market_query, regions, bookmakers)
        if data: all_rows.extend(parse_event_props(data))
    return consensus_lines(merge_over_under_rows(all_rows)), events

def load_custom_projection_db():
    data = load_json(CUSTOM_STATS_FILE, {})
    return data if isinstance(data, dict) else {}

def save_custom_projection_db(data): save_json(CUSTOM_STATS_FILE, data)

def projection_db_combined():
    db = dict(DEFAULT_PROJECTION_DB)
    custom = load_custom_projection_db()
    for k, v in custom.items(): db[k] = v
    return db

def lookup_projection_stats(player, db):
    best_key, best_score = None, 0.0
    for k in db.keys():
        sc = name_score(player, k)
        if sc > best_score:
            best_score, best_key = sc, k
    if best_key and best_score >= 0.82:
        return db.get(best_key), best_score, best_key
    return None, best_score, best_key

def market_stat_value(stats, market):
    pts = safe_float(stats.get("points", stats.get("avg_pts", 0)), 0) or 0
    reb = safe_float(stats.get("rebounds", stats.get("avg_reb", 0)), 0) or 0
    ast = safe_float(stats.get("assists", stats.get("avg_ast", 0)), 0) or 0
    threes = safe_float(stats.get("threes", stats.get("avg_3pm", 0)), 0) or 0
    stl = safe_float(stats.get("steals", stats.get("avg_stl", 0)), 0) or 0
    blk = safe_float(stats.get("blocks", stats.get("avg_blk", 0)), 0) or 0
    return {
        "player_points": pts, "player_rebounds": reb, "player_assists": ast,
        "player_threes": threes, "player_steals": stl, "player_blocks": blk,
        "player_points_rebounds_assists": pts + reb + ast,
        "player_points_rebounds": pts + reb,
        "player_points_assists": pts + ast,
        "player_rebounds_assists": reb + ast,
    }.get(market)

def player_market_key(player, market): return f"{normalize_name(player)}::{market}"

def apply_learning(player, market, proj):
    data = load_json(LEARN_FILE, {})
    rec = data.get(player_market_key(player, market), {})
    scale = safe_float(rec.get("scale"), 1.0) or 1.0
    samples = safe_int(rec.get("samples"), 0) or 0
    residual = safe_float(rec.get("avg_residual"), 0.0) or 0.0
    if samples < 4: return proj, "Learning warming up"
    adjusted = (proj * scale) + clamp(residual * 0.25, -1.25, 1.25)
    return float(max(0, adjusted)), f"Learning x{scale:.3f}, residual {residual:+.2f}, n={samples}"

def update_learning(player, market, projected, actual):
    data = load_json(LEARN_FILE, {})
    key = player_market_key(player, market)
    rec = data.get(key, {"scale": 1.0, "samples": 0, "avg_residual": 0.0})
    projected, actual = safe_float(projected), safe_float(actual)
    if projected is None or projected <= 0 or actual is None: return rec
    old_scale = safe_float(rec.get("scale"), 1.0) or 1.0
    old_samples = safe_int(rec.get("samples"), 0) or 0
    old_resid = safe_float(rec.get("avg_residual"), 0.0) or 0.0
    err_pct = clamp((actual - projected) / max(projected, 1.0), -0.40, 0.40)
    resid = actual - projected
    rec.update({
        "scale": clamp(old_scale * (1 + 0.04 * err_pct), 0.90, 1.10),
        "samples": old_samples + 1,
        "avg_residual": round(((old_resid * old_samples) + resid) / max(old_samples + 1, 1), 3),
        "last_error_pct": round(err_pct, 4), "last_projected": projected,
        "last_actual": actual, "updated_at": now_iso(),
    })
    data[key] = rec
    save_json(LEARN_FILE, data)
    return rec

def estimate_projection(row, db):
    player, market = row["Player"], row["Market"]
    line = safe_float(row["Line"], 0.0) or 0.0
    stats, match_score, matched_name = lookup_projection_stats(player, db)
    notes = []
    if stats:
        base = market_stat_value(stats, market)
        pace = safe_float(stats.get("pace", stats.get("pace_factor", 1.0)), 1.0) or 1.0
        dvp = safe_float(stats.get("dvp", stats.get("dvp_adjustment", 1.0)), 1.0) or 1.0
        if base is None:
            proj, data_score = line, 48
            notes.append("Stats match but market stat missing; anchored to real line")
        else:
            proj = float(base) * pace * dvp
            data_score = 78 + int(min(12, match_score * 12))
            notes.append(f"Projection DB match: {matched_name} ({match_score:.2f})")
            notes.append(f"pace x{pace:.3f}, dvp x{dvp:.3f}")
    else:
        proj, data_score = line, 42
        notes.append("No projection stat match; anchored to real line with low confidence")
    gap = abs(proj - line)
    if gap > max(2.5, 0.27 * max(line, 1.0)):
        proj = (proj * 0.72) + (line * 0.28)
        data_score -= 6
        notes.append("Large projection/market gap; conservative blend toward market")
    proj, learn_note = apply_learning(player, market, proj)
    notes.append(learn_note)
    std = MARKET_STD.get(market, 4.5)
    if data_score < 60: std *= 1.25
    return float(max(0, proj)), float(std), int(clamp(data_score, 0, 100)), "; ".join(notes)

def update_clv_snapshot(player, market, book, line):
    data = load_json(CLV_FILE, {})
    key = f"{today_str()}::{normalize_name(player)}::{market}::{book}"
    line = float(line)
    old = data.get(key)
    if not old:
        data[key] = {"player": player, "market": market, "book": book, "open_line": line, "latest_line": line, "last_updated": now_iso()}
        save_json(CLV_FILE, data)
        return 0.0
    open_line = safe_float(old.get("open_line"), line)
    old["latest_line"], old["last_updated"] = line, now_iso()
    data[key] = old
    save_json(CLV_FILE, data)
    return round(line - open_line, 2)

def track_line_history(player, market, book, line):
    hist = load_json(LINE_HISTORY_FILE, {})
    key = f"{normalize_name(player)}::{market}::{book}"
    rows = hist.get(key, [])
    rows.append({"t": now_iso(), "line": safe_float(line)})
    hist[key] = rows[-40:]
    save_json(LINE_HISTORY_FILE, hist)
    if len(hist[key]) < 2: return 0.0
    first, last = safe_float(hist[key][0].get("line")), safe_float(hist[key][-1].get("line"))
    if first is None or last is None: return 0.0
    return round(last - first, 2)

def classify_signal(proj, line, prob, ev, data_score, book_count, alt_line):
    edge = abs(proj - line)
    notes = []
    if data_score < 55: notes.append("Low projection-data confidence")
    if book_count < 2: notes.append("Single-book line")
    if alt_line: notes.append("Alternate/non-consensus line")
    if edge < 0.35: notes.append("Projection too close to line")
    if prob < 0.54: notes.append("Weak fair probability")
    if data_score >= 88 and prob >= 0.62 and edge >= 0.90 and ev is not None and ev > 0:
        return "ELITE WATCH", notes or ["All strict gates passed"]
    if data_score >= 78 and prob >= 0.57 and edge >= 0.55 and ev is not None and ev > 0:
        return "PASS", notes or ["Bettable gates passed"]
    if data_score >= 62 and prob >= 0.54 and edge >= 0.35:
        return "LEAN", notes or ["Some gates passed"]
    return "NO BET", notes or ["Protection gates did not pass"]



def manual_line_key(player, market, book=""):
    # Book optional. Blank book = applies to all books for player+market.
    return f"{normalize_name(player)}::{market}::{str(book or '').lower().strip()}"

def load_manual_lines():
    data = load_json(MANUAL_LINES_FILE, {})
    return data if isinstance(data, dict) else {}

def save_manual_lines(data):
    save_json(MANUAL_LINES_FILE, data)

def get_manual_line_override(player, market, book):
    data = load_manual_lines()

    # Exact book override first.
    exact = data.get(manual_line_key(player, market, book))
    if exact and safe_float(exact.get("manual_line")) is not None:
        return safe_float(exact.get("manual_line")), exact.get("note", ""), "BOOK"

    # Global player+market override second.
    global_key = manual_line_key(player, market, "")
    global_rec = data.get(global_key)
    if global_rec and safe_float(global_rec.get("manual_line")) is not None:
        return safe_float(global_rec.get("manual_line")), global_rec.get("note", ""), "GLOBAL"

    return None, "", ""

def set_manual_line_override(player, market, manual_line, book="", note=""):
    data = load_manual_lines()
    key = manual_line_key(player, market, book)
    data[key] = {
        "player": player,
        "market": market,
        "book": book,
        "manual_line": float(manual_line),
        "note": note,
        "updated_at": now_iso(),
    }
    save_manual_lines(data)
    return key

def clear_manual_line_override(player, market, book=""):
    data = load_manual_lines()
    key = manual_line_key(player, market, book)
    if key in data:
        data.pop(key)
        save_manual_lines(data)
        return True
    return False


def market_confidence_score(book_count, alt_line, over_price, under_price, clv_delta, line_delta):
    """MLB-style market quality score for WNBA props."""
    score = 50
    book_count = safe_int(book_count, 1) or 1

    if book_count >= 5:
        score += 22
    elif book_count >= 3:
        score += 15
    elif book_count >= 2:
        score += 8
    else:
        score -= 8

    if alt_line:
        score -= 12

    # Better if both sides have prices.
    if safe_float(over_price) is not None and safe_float(under_price) is not None:
        score += 8

    # Stable line is good; large moves require caution.
    if abs(safe_float(line_delta, 0) or 0) >= 1.5:
        score -= 10
    elif abs(safe_float(line_delta, 0) or 0) >= 1.0:
        score -= 5

    # CLV movement exists but not crazy.
    if abs(safe_float(clv_delta, 0) or 0) <= 0.5:
        score += 5

    return int(clamp(score, 0, 100))

def volatility_rating(market, line, data_score, book_count, alt_line):
    """MLB-style risk/volatility label."""
    risk = 0
    if market in ["player_steals", "player_blocks", "player_threes"]:
        risk += 2
    if market in ["player_points_rebounds_assists", "player_points_rebounds", "player_points_assists", "player_rebounds_assists"]:
        risk += 1
    if data_score < 60:
        risk += 2
    if (safe_int(book_count, 1) or 1) < 2:
        risk += 1
    if alt_line:
        risk += 1
    if safe_float(line, 0) is not None and safe_float(line, 0) <= 1.5:
        risk += 1

    if risk >= 5:
        return "HIGH"
    if risk >= 3:
        return "MEDIUM"
    return "LOW"

def steam_signal(edge, line_delta, clv_delta, pick):
    """Simple line-movement signal, similar to MLB CLV/steam logic."""
    line_delta = safe_float(line_delta, 0) or 0
    clv_delta = safe_float(clv_delta, 0) or 0

    # If line moved upward, over got harder and under got better number earlier.
    if pick == "OVER" and line_delta > 0.5:
        return "AGAINST OVER STEAM"
    if pick == "UNDER" and line_delta < -0.5:
        return "AGAINST UNDER STEAM"
    if pick == "OVER" and line_delta < -0.5:
        return "FAVORABLE OVER CLV"
    if pick == "UNDER" and line_delta > 0.5:
        return "FAVORABLE UNDER CLV"
    if abs(clv_delta) >= 1.0:
        return "LINE MOVED"
    return "STABLE"

def overall_prop_rating(data_score, market_confidence, fair_prob, abs_edge, volatility, signal):
    """Weighted rating inspired by the MLB app's overall score."""
    rating = 0
    rating += (safe_float(data_score, 0) or 0) * 0.36
    rating += (safe_float(market_confidence, 0) or 0) * 0.28
    rating += (safe_float(fair_prob, 50) or 50) * 0.24
    rating += min((safe_float(abs_edge, 0) or 0) * 8, 12)

    if volatility == "HIGH":
        rating -= 8
    elif volatility == "MEDIUM":
        rating -= 3

    if signal == "ELITE WATCH":
        rating += 5
    elif signal == "PASS":
        rating += 3
    elif signal == "NO BET":
        rating -= 5

    return round(clamp(rating, 0, 100), 1)

def protection_tag(signal, volatility, market_confidence, edge, fair_prob):
    """Clear MLB-style final tag."""
    if signal in ["ELITE WATCH", "PASS"] and volatility == "LOW" and market_confidence >= 70:
        return "CLEAN"
    if signal in ["ELITE WATCH", "PASS"] and volatility != "HIGH":
        return "PLAYABLE"
    if signal == "LEAN":
        return "LEAN ONLY"
    return "PROTECTED NO BET"



def default_market_for_projection_board():
    return ["player_points", "player_rebounds", "player_assists", "player_threes", "player_points_rebounds_assists"]

def projection_only_rows_from_db(db, events=None, selected_markets=None):
    """Create automatic player cards even when no sportsbook player props are returned.

    These rows do not invent sportsbook lines. They show projection cards with Line=None.
    If real lines come in later, normal real-line cards will appear.
    """
    rows = []
    markets = selected_markets or default_market_for_projection_board()
    matchup = "Projection Board"
    game_day = "Today"
    if events:
        try:
            first = events[0]
            matchup = f"{first.get('away_team','')} @ {first.get('home_team','')}".strip(" @") or "Projection Board"
            game_day = utc_to_local_day_label(first.get("commence_time", ""))
        except Exception:
            pass

    for player, stats in db.items():
        if is_bad_player_name(player):
            continue
        for market in markets:
            if market not in MARKET_MAP:
                continue
            proj_val = market_stat_value(stats, market)
            if proj_val is None:
                continue
            rows.append({
                "Event ID": "projection_board",
                "Game Day": game_day,
                "Commence Time": "",
                "Matchup": matchup,
                "Home Team": "",
                "Away Team": "",
                "Book": "No Line Yet",
                "Book Key": "projection_board",
                "Market": market,
                "Market Label": MARKET_MAP.get(market, market),
                "Player": player,
                "Line": None,
                "Price": -110,
                "Over Price": None,
                "Under Price": None,
                "Source": "Projection Board",
                "Real Line": False,
                "Book Count": 0,
                "Consensus Line": None,
                "Books": "No sportsbook line",
                "Alt Line": False,
                "Projection Only": True,
            })
    return rows


def build_board(prop_rows, db):
    board = []
    for r in prop_rows:
        player = r["Player"]
        if is_bad_player_name(player): continue
        original_line = safe_float(r.get("Line"))
        projection_only = bool(r.get("Projection Only")) or original_line is None

        manual_line, manual_note, manual_scope = get_manual_line_override(player, r["Market"], r.get("Book", ""))
        line = manual_line if manual_line is not None else original_line

        # Projection is calculated from the projection DB and is not changed by manual lines.
        if projection_only:
            # For no-line cards, calculate projection directly from DB without market anchoring.
            stats, match_score, matched_name = lookup_projection_stats(player, db)
            if stats:
                base = market_stat_value(stats, r["Market"])
                pace = safe_float(stats.get("pace", stats.get("pace_factor", 1.0)), 1.0) or 1.0
                dvp = safe_float(stats.get("dvp", stats.get("dvp_adjustment", 1.0)), 1.0) or 1.0
                proj = float(base or 0) * pace * dvp
                data_score = 78 + int(min(12, match_score * 12))
                proj_notes = f"Projection board only: {matched_name} ({match_score:.2f}); no sportsbook line returned yet"
            else:
                proj, data_score, proj_notes = 0.0, 30, "Projection board only; no stat match"
            proj, learn_note = apply_learning(player, r["Market"], proj)
            proj_notes += f"; {learn_note}"
            std = MARKET_STD.get(r["Market"], 4.5)
            side = "NO LINE"
            prob = 0.50
        else:
            # IMPORTANT:
            # Projection is calculated from the original sportsbook line context,
            # not from manual line overrides. Manual lines only affect edge/pick/EV/rating.
            proj, std, data_score, proj_notes = estimate_projection(r, db)
            if manual_line is not None:
                proj_notes += f"; Manual line override active ({manual_scope}) — projection unchanged"
            side = "OVER" if proj > line else "UNDER"
            prob = normal_side_probability(proj, line, std, side)
        if projection_only:
            price = None
            ev = None
            kelly = 0.0
        else:
            price = safe_float(r.get("Over Price" if side == "OVER" else "Under Price"), safe_float(r.get("Price"), -110)) or -110
            ev = expected_value(prob, price)
            kelly = min(kelly_fraction(prob, price), 0.02)
        if projection_only:
            clv_delta = 0.0
            line_delta = 0.0
            book_count = 0
            alt_line = False
            mkt_conf = 0
            volatility = "NO LINE"
            signal = "NO LINE"
            risk_notes = ["No sportsbook/player-prop line returned yet"]
            steam = "NO LINE"
            overall_rating = round(clamp(data_score * 0.55, 0, 100), 1)
            protect = "PROJECTION ONLY"
            edge_val = None
            abs_edge_val = None
        else:
            clv_delta = update_clv_snapshot(player, r["Market"], r["Book"], original_line)
            line_delta = track_line_history(player, r["Market"], r["Book"], original_line)

            book_count = safe_int(r.get("Book Count"), 1) or 1
            alt_line = bool(r.get("Alt Line"))
            mkt_conf = market_confidence_score(book_count, alt_line, r.get("Over Price"), r.get("Under Price"), clv_delta, line_delta)
            volatility = volatility_rating(r["Market"], line, data_score, book_count, alt_line)

            signal, risk_notes = classify_signal(proj, line, prob, ev, data_score, book_count, alt_line)

            steam = steam_signal(proj - line, line_delta, clv_delta, side)
            overall_rating = overall_prop_rating(data_score, mkt_conf, round(prob * 100, 1), abs(proj - line), volatility, signal)
            protect = protection_tag(signal, volatility, mkt_conf, abs(proj - line), round(prob * 100, 1))
            edge_val = round(proj - line, 2)
            abs_edge_val = round(abs(proj - line), 2)

        board.append({
            "Player": player, "Game Day": r.get("Game Day", "Unknown"), "Matchup": r.get("Matchup", ""),
            "Book": r.get("Book", ""), "Books": r.get("Books", r.get("Book", "")), "Book Count": r.get("Book Count", 1),
            "Market": r["Market"], "Market Label": r.get("Market Label", MARKET_MAP.get(r["Market"], r["Market"])),
            "Line": line if line is not None else "No Line", "Book Line": original_line if original_line is not None else "No Line",
            "Manual Line Active": manual_line is not None, "Projection Only": projection_only,
            "Manual Line Note": manual_note, "Consensus Line": r.get("Consensus Line", original_line) if original_line is not None else "No Line", "Projection": round(proj, 2),
            "Edge": edge_val, "Abs Edge": abs_edge_val, "Pick": side,
            "Fair Prob": round(prob * 100, 1), "EV": round(ev * 100, 1) if ev is not None else None,
            "Kelly": round(kelly * 100, 2), "Data Score": data_score, "Market Confidence": mkt_conf,
            "Overall Rating": overall_rating, "Volatility": volatility, "Steam Signal": steam,
            "Protection Tag": protect, "Signal": signal, "Price": price,
            "Over Price": r.get("Over Price"), "Under Price": r.get("Under Price"), "Alt Line": alt_line,
            "CLV Δ": clv_delta, "Line Δ": line_delta, "Risk Notes": "; ".join(risk_notes),
            "Projection Notes": proj_notes, "Source": "The Odds API", "Commence Time": r.get("Commence Time"),
            "Event ID": r.get("Event ID"), "Saved At": now_iso(), "App Version": APP_VERSION,
        })
    df = pd.DataFrame(board)
    if not df.empty:
        ranks = {"ELITE WATCH": 0, "PASS": 1, "LEAN": 2, "NO BET": 3}
        df["_rank"] = df["Signal"].map(ranks).fillna(9)
        df["_abs_sort"] = pd.to_numeric(df["Abs Edge"], errors="coerce").fillna(-1)
        df = df.sort_values(["_rank", "Overall Rating", "Data Score", "_abs_sort"], ascending=[True, False, False, False]).drop(columns=["_rank", "_abs_sort"])
    return df

def save_official_snapshots(rows, tag="before"):
    existing = load_json(PICK_LOG, [])
    ba = load_json(BEFORE_AFTER_FILE, [])
    count = 0
    for row in rows or []:
        rec = dict(row)
        rec["Snapshot Type"], rec["Snapshot Date"] = tag, today_str()
        rec["Official ID"] = f"{today_str()}::{normalize_name(rec.get('Player'))}::{rec.get('Market')}::{rec.get('Book')}::{rec.get('Line')}::{tag}"
        if not any(x.get("Official ID") == rec["Official ID"] for x in existing):
            existing.append(rec); count += 1
        ba.append(rec)
    save_json(PICK_LOG, existing[-30000:])
    save_json(BEFORE_AFTER_FILE, ba[-40000:])
    return count

def grade_pick(row, actual):
    actual, line, pick = safe_float(actual), safe_float(row.get("Line")), row.get("Pick")
    if actual is None or line is None or pick not in ["OVER", "UNDER"]: return None
    if pick == "OVER": return "WIN" if actual > line else "LOSS" if actual < line else "PUSH"
    return "WIN" if actual < line else "LOSS" if actual > line else "PUSH"

def save_grade(player, market, line, actual, book_filter=""):
    picks = load_json(PICK_LOG, [])
    results = load_json(RESULT_LOG, [])
    matches = []
    for r in reversed(picks):
        if normalize_name(r.get("Player")) == normalize_name(player) and r.get("Market") == market:
            if book_filter and str(r.get("Book", "")).lower() != book_filter.lower(): continue
            if safe_float(r.get("Line")) == safe_float(line): matches.append(r)
    count = 0
    for r in matches[:8]:
        result = grade_pick(r, actual)
        if result is None: continue
        out = dict(r)
        out.update({"Actual": safe_float(actual), "Graded Result": result, "Graded At": now_iso()})
        results.append(out)
        update_learning(out.get("Player"), out.get("Market"), out.get("Projection"), actual)
        count += 1
    save_json(RESULT_LOG, results[-30000:])
    return count

def render_game_cards(events):
    if not events:
        st.info("No WNBA events loaded. Check your ODDS_API_KEY or season schedule.")
        return
    for g in events:
        st.markdown(f"""
        <div class="game-card">
            <b>{g.get('away_team', '')} @ {g.get('home_team', '')}</b><br>
            <span class="small-muted">{utc_to_local_day_label(g.get('commence_time'))} • {g.get('commence_time', '')} • Event ID {g.get('id', '')}</span>
        </div>
        """, unsafe_allow_html=True)

def render_player_cards(df, max_cards=200):
    if df.empty:
        st.info("No props match your filters.")
        return

    def fmt_num(value, digits=2, signed=False):
        try:
            if value is None or pd.isna(value):
                return "—"
            f = float(value)
            return f"{f:+.{digits}f}" if signed else f"{f:.{digits}f}"
        except Exception:
            return "—"

    def fmt_pct(value):
        try:
            if value is None or pd.isna(value):
                return "—"
            return f"{float(value):.1f}%"
        except Exception:
            return "—"

    for _, row in df.head(max_cards).iterrows():
        sig = row.get("Signal", "NO LINE")
        card = "green-card" if sig in ["ELITE WATCH", "PASS"] else "warn-card" if sig == "LEAN" else "clean-card"
        badge = "good-badge" if sig in ["ELITE WATCH", "PASS"] else "yellow-badge" if sig == "LEAN" else "red-badge"
        alt_badge = '<span class="badge yellow-badge">ALT LINE</span>' if row.get("Alt Line") else ""

        line_display = row.get("Line", "No Line")
        book_line_display = row.get("Book Line", line_display)
        consensus_display = row.get("Consensus Line", line_display)
        projection_display = fmt_num(row.get("Projection"), 2)
        edge_display = fmt_num(row.get("Edge"), 2, signed=True)
        fair_prob_display = fmt_pct(row.get("Fair Prob"))
        ev_display = fmt_pct(row.get("EV"))
        rating_display = row.get("Overall Rating", row.get("Data Score", "—"))
        market_conf = row.get("Market Confidence", "—")
        volatility = row.get("Volatility", "—")
        over_price = row.get("Over Price", "—")
        under_price = row.get("Under Price", "—")
        clv_delta = row.get("CLV Δ", "—")
        line_delta = row.get("Line Δ", "—")
        kelly = row.get("Kelly", "—")
        steam = row.get("Steam Signal", "—")
        protection = row.get("Protection Tag", "—")
        manual_active = row.get("Manual Line Active", False)

        st.markdown(f"""
        <div class="{card}">
            <div style="display:flex;justify-content:space-between;gap:12px;align-items:flex-start;">
                <div>
                    <div style="font-size:23px;font-weight:950;">{row.get('Player','')}</div>
                    <div class="small-muted">{row.get('Game Day','')} • {row.get('Matchup','')} • {row.get('Market Label','')} • {row.get('Book','')}</div>
                </div>
                <div><span class="badge {badge}">{sig}</span>{alt_badge}</div>
            </div>
            <div class="kpi-strip">
                <div class="kpi-box"><div class="kpi-label">Projection</div><div class="kpi-value">{projection_display}</div></div>
                <div class="kpi-box"><div class="kpi-label">Line</div><div class="kpi-value">{line_display}</div><div class="kpi-sub">Book {book_line_display} • Consensus {consensus_display}</div></div>
                <div class="kpi-box"><div class="kpi-label">Edge</div><div class="kpi-value">{edge_display}</div></div>
                <div class="kpi-box"><div class="kpi-label">Pick</div><div class="kpi-value">{row.get('Pick','NO LINE')}</div></div>
                <div class="kpi-box"><div class="kpi-label">Fair Prob</div><div class="kpi-value">{fair_prob_display}</div><div class="kpi-sub">EV {ev_display}</div></div>
                <div class="kpi-box"><div class="kpi-label">Rating</div><div class="kpi-value">{rating_display}/100</div><div class="kpi-sub">Mkt {market_conf} • {volatility}</div></div>
            </div>
            <div class="small-muted"><b>Prices:</b> Over {over_price} / Under {under_price} • <b>CLV Δ:</b> {clv_delta} • <b>Line Δ:</b> {line_delta} • <b>Steam:</b> {steam} • <b>Kelly:</b> {kelly}%</div>
            <div class="small-muted"><b>Protection:</b> {protection} • <b>Volatility:</b> {volatility} • <b>Market Confidence:</b> {market_conf}/100 • <b>Manual Line:</b> {manual_active}</div>
            <div class="small-muted"><b>Risk:</b> {row.get('Risk Notes','')}</div>
            <div class="small-muted"><b>Model:</b> {row.get('Projection Notes','')}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown(f"""
<div class="hero-panel">
  <div class="big-title">🏀 WNBA Prop Engine</div>
  <div class="sub-title">Clean rebuild using The Odds API event-odds • Full player-card board • Before/After saves • Grading + learning</div>
  <span class="badge good-badge">{APP_VERSION}</span>
  <span class="badge blue-badge">Sport: basketball_wnba</span>
  <span class="badge">Real lines only</span>
  <span class="badge red-badge">NBA leak blocker</span>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("Setup")
    api_key_input = st.text_input("The Odds API Key", value=get_api_key(), type="password")
    regions = st.text_input("Regions", value="us")
    bookmakers = st.text_input("Optional bookmakers filter", value="", help="Example: draftkings,fanduel,betmgm")
    days_ahead = st.slider("Events through next N days", 1, 7, 2)

    st.divider()
    st.caption("Markets")
    market_labels_to_keys = {v: k for k, v in MARKET_MAP.items()}
    default_market_labels = ["Points", "Rebounds", "Assists", "3PT Made", "Pts + Rebs + Asts"]
    selected_market_labels = st.multiselect("Player prop markets", list(MARKET_MAP.values()), default=[m for m in default_market_labels if m in MARKET_MAP.values()])
    selected_market_keys = [market_labels_to_keys[x] for x in selected_market_labels]

    st.divider()
    board_filter = st.radio("Board filter", ["All Lines", "Today", "Tomorrow"], horizontal=True)
    signal_filter = st.multiselect("Signals", ["ELITE WATCH", "PASS", "LEAN", "NO BET", "NO LINE"], default=["ELITE WATCH", "PASS", "LEAN", "NO BET", "NO LINE"])
    book_filter = st.text_input("Filter book contains", value="")
    search_name = st.text_input("Optional player filter", value="")
    max_cards = st.slider("Max cards", 25, 500, 200)

    st.divider()
    save_tag = st.selectbox("Snapshot type", ["before", "after"], index=0)
    only_save = st.multiselect("Save only signals", ["ELITE WATCH", "PASS", "LEAN", "NO BET"], default=["ELITE WATCH", "PASS", "LEAN"])
    refresh = st.button("🔄 Refresh / Load Board", use_container_width=True)
    st.caption("If no players show, open the Logs tab to see API status/errors.")

if refresh:
    st.cache_data.clear()

if "loaded_once" not in st.session_state:
    st.session_state.loaded_once = True
    auto_load = bool(api_key_input)
else:
    auto_load = False

should_load = refresh or auto_load

if not api_key_input:
    st.markdown("""
    <div class="red-card">
    <b>Add your The Odds API key in the sidebar.</b><br>
    Railway: add environment variable <code>ODDS_API_KEY</code>. Streamlit Cloud: add secret <code>ODDS_API_KEY="..."</code>.
    </div>
    """, unsafe_allow_html=True)

if should_load and api_key_input:
    with st.spinner("Loading WNBA events and real player props from The Odds API..."):
        api_props, events = fetch_all_real_props(api_key_input, selected_market_keys, regions, bookmakers, days_ahead)
        manual_props = load_manual_props()
        db_now = projection_db_combined()
        projection_rows = projection_only_rows_from_db(db_now, events, selected_market_keys)

        # Always show player cards. Real/API/manual line cards appear first when available;
        # projection-only cards fill the board when no sportsbook prop line is returned.
        raw_props = api_props + manual_props
        if not raw_props:
            raw_props = projection_rows
        else:
            # Add projection-only cards for players/markets that do not have a line yet.
            existing_keys = set((normalize_name(x.get("Player")), x.get("Market")) for x in raw_props)
            raw_props += [x for x in projection_rows if (normalize_name(x.get("Player")), x.get("Market")) not in existing_keys]

        board_df = build_board(raw_props, db_now)
        st.session_state["events"] = events
        st.session_state["raw_props"] = raw_props
        st.session_state["board_df"] = board_df
        st.session_state["last_loaded"] = now_iso()

events = st.session_state.get("events", [])
board_df = st.session_state.get("board_df", pd.DataFrame())
last_loaded = st.session_state.get("last_loaded", "Not loaded")

if api_key_input and board_df.empty:
    st.markdown(f"""
    <div class="warn-card">
    <b>No sportsbook player props returned yet.</b><br>
    Click Refresh / Load Board. If still empty, check the Logs tab. Most common causes: The Odds API key does not include player-prop markets, selected markets are not available yet, or the WNBA games for today/tomorrow have no posted player props.<br>
    Last loaded: {last_loaded}<br>
    Tip: try selecting only Points/Rebounds/Assists first and clear the bookmaker filter. You can also use the Manual Props tab to enter Underdog lines manually.
    </div>
    """, unsafe_allow_html=True)

if not board_df.empty:
    filt = board_df.copy()
    if board_filter in ["Today", "Tomorrow"] and "Game Day" in filt.columns:
        filt = filt[filt["Game Day"].astype(str).isin([board_filter, "Unknown"])]
    if signal_filter:
        filt = filt[filt["Signal"].isin(signal_filter)]
    if book_filter.strip():
        filt = filt[filt["Book"].str.lower().str.contains(book_filter.lower(), na=False)]
    if search_name.strip():
        filt = filt[filt["Player"].str.lower().str.contains(search_name.lower(), na=False)]

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Props shown", len(filt)); c2.metric("Raw real lines", len(board_df))
    c3.metric("Elite", int((filt["Signal"] == "ELITE WATCH").sum()))
    c4.metric("Pass", int((filt["Signal"] == "PASS").sum()))
    c5.metric("Lean", int((filt["Signal"] == "LEAN").sum()))
    c6.metric("Events", len(events))

    save_rows = filt[filt["Signal"].isin(only_save)].to_dict("records") if only_save else filt.to_dict("records")
    if st.button(f"💾 Save official {save_tag} snapshots", use_container_width=True):
        n = save_official_snapshots(save_rows, tag=save_tag)
        st.success(f"Saved {n} official {save_tag} snapshots.")

    tab_cards, tab_table, tab_games, tab_saved, tab_grade, tab_learning, tab_manual_props, tab_manual, tab_stats, tab_logs = st.tabs(["🃏 Player Cards", "📋 Prop Table", "📅 Games", "💾 Saved/CLV", "✅ Grade", "🧠 Learning", "➕ Manual Props", "✏️ Manual Line", "📥 Projection DB", "🧾 Logs"])

    with tab_cards:
        render_player_cards(filt, max_cards=max_cards)

    with tab_table:
        cols = ["Player", "Game Day", "Matchup", "Book", "Market Label", "Line", "Book Line", "Projection Only", "Manual Line Active", "Consensus Line", "Projection", "Edge", "Pick", "Fair Prob", "EV", "Kelly", "Data Score", "Market Confidence", "Overall Rating", "Volatility", "Steam Signal", "Protection Tag", "Signal", "Book Count", "Alt Line", "Over Price", "Under Price", "CLV Δ", "Line Δ", "Risk Notes", "Projection Notes"]
        safe_cols = [c for c in cols if c in filt.columns]
        st.dataframe(filt[safe_cols], use_container_width=True, height=740)
        st.download_button("Download board CSV", filt[safe_cols].to_csv(index=False).encode("utf-8"), "wnba_oddsapi_board.csv", "text/csv")

    with tab_games:
        render_game_cards(events)

    with tab_manual_props_empty:
        st.subheader("Manual Prop Board")
        st.caption("Games are loading but player props are not. Enter real lines manually from Underdog or another book.")

        inv_market_manual = {v: k for k, v in MARKET_MAP.items()}
        current_manual = load_manual_props()
        if current_manual:
            st.dataframe(pd.DataFrame(current_manual), use_container_width=True, height=260)
        else:
            st.info("No manual props added yet.")

        with st.form("manual_prop_add_form_empty"):
            mp_player = st.text_input("Player", value="", placeholder="Jackie Young")
            mp_market_label = st.selectbox("Market", list(MARKET_MAP.values()), key="manual_prop_market_empty")
            mp_line = st.number_input("Line", min_value=0.0, max_value=150.0, step=0.5, value=15.5, key="manual_prop_line_empty")
            mp_book = st.text_input("Book / Source", value="Underdog", key="manual_prop_book_empty")
            mp_matchup = st.text_input("Matchup optional", value="Manual Entry", key="manual_prop_match_empty")
            mp_day = st.selectbox("Game day label", ["Manual", "Today", "Tomorrow"], index=0, key="manual_prop_day_empty")
            c_ov, c_un = st.columns(2)
            mp_over_price = c_ov.number_input("Over price", value=-110, step=1, key="manual_over_empty")
            mp_under_price = c_un.number_input("Under price", value=-110, step=1, key="manual_under_empty")
            mp_note = st.text_input("Note optional", value="", key="manual_prop_note_empty")
            submitted_manual_prop = st.form_submit_button("Add manual prop to board")

            if submitted_manual_prop:
                if not mp_player.strip():
                    st.warning("Enter a player name.")
                else:
                    add_manual_prop(mp_player.strip(), inv_market_manual[mp_market_label], mp_line, mp_book.strip(), mp_matchup.strip(), mp_day, mp_over_price, mp_under_price, mp_note.strip())
                    st.success("Manual prop added. Hit Refresh / Load Board to show it on player cards.")

        if st.button("Clear ALL manual props", use_container_width=True, key="clear_manual_props_empty"):
            clear_manual_props()
            st.success("Manual props cleared. Refresh board.")



    with tab_saved:
        saved = pd.DataFrame(load_json(PICK_LOG, []))
        clv = pd.DataFrame(load_json(CLV_FILE, {}).values())
        st.subheader("Official saved snapshots")
        if not saved.empty: st.dataframe(saved.tail(700), use_container_width=True, height=350)
        else: st.info("No saved snapshots yet.")
        st.subheader("CLV tracker")
        if not clv.empty: st.dataframe(clv.tail(700), use_container_width=True, height=300)
        else: st.info("No CLV rows yet.")

    with tab_grade:
        inv_market = {v: k for k, v in MARKET_MAP.items()}
        with st.form("grade_form"):
            g_player = st.text_input("Player name")
            g_market_label = st.selectbox("Market", list(MARKET_MAP.values()))
            g_line = st.number_input("Saved line", min_value=0.0, max_value=120.0, step=0.5)
            g_actual = st.number_input("Actual result", min_value=0.0, max_value=160.0, step=0.5)
            g_book = st.text_input("Book filter optional", value="")
            submitted = st.form_submit_button("Grade and update learning")
            if submitted:
                n = save_grade(g_player, inv_market[g_market_label], g_line, g_actual, g_book)
                if n: st.success(f"Graded {n} saved snapshot(s) and updated learning.")
                else: st.warning("No matching saved snapshot found.")
        results = pd.DataFrame(load_json(RESULT_LOG, []))
        if not results.empty: st.dataframe(results.tail(700), use_container_width=True, height=360)
        else: st.info("No graded results yet.")

    with tab_learning:
        learn = load_json(LEARN_FILE, {})
        if not learn:
            st.info("Learning file is empty until you grade results.")
        else:
            rows = []
            for k, v in learn.items():
                player, market = k.split("::", 1) if "::" in k else (k, "")
                rows.append({"Player": player, "Market": market, "Scale": v.get("scale"), "Samples": v.get("samples"), "Avg Residual": v.get("avg_residual"), "Updated": v.get("updated_at")})
            st.dataframe(pd.DataFrame(rows), use_container_width=True, height=520)


    with tab_manual_props:
        st.subheader("Manual Prop Board")
        st.caption("Use this when The Odds API shows games but no player props. Enter real lines manually from Underdog or another book. Projection stays unchanged.")

        inv_market_manual = {v: k for k, v in MARKET_MAP.items()}

        current_manual = load_manual_props()
        if current_manual:
            st.write("Manual props currently active")
            st.dataframe(pd.DataFrame(current_manual), use_container_width=True, height=260)
        else:
            st.info("No manual props added yet.")

        with st.form("manual_prop_add_form"):
            mp_player = st.text_input("Player", value="", placeholder="Jackie Young")
            mp_market_label = st.selectbox("Market", list(MARKET_MAP.values()), key="manual_prop_market")
            mp_line = st.number_input("Line", min_value=0.0, max_value=150.0, step=0.5, value=15.5)
            mp_book = st.text_input("Book / Source", value="Underdog")
            mp_matchup = st.text_input("Matchup optional", value="Manual Entry")
            mp_day = st.selectbox("Game day label", ["Manual", "Today", "Tomorrow"], index=0)
            c_ov, c_un = st.columns(2)
            mp_over_price = c_ov.number_input("Over price", value=-110, step=1)
            mp_under_price = c_un.number_input("Under price", value=-110, step=1)
            mp_note = st.text_input("Note optional", value="")
            submitted_manual_prop = st.form_submit_button("Add manual prop to board")

            if submitted_manual_prop:
                if not mp_player.strip():
                    st.warning("Enter a player name.")
                else:
                    add_manual_prop(
                        mp_player.strip(),
                        inv_market_manual[mp_market_label],
                        mp_line,
                        mp_book.strip(),
                        mp_matchup.strip(),
                        mp_day,
                        mp_over_price,
                        mp_under_price,
                        mp_note.strip(),
                    )
                    st.success("Manual prop added. Hit Refresh / Load Board to show it on player cards.")

        c_clear, c_refresh_note = st.columns(2)
        if c_clear.button("Clear ALL manual props", use_container_width=True):
            clear_manual_props()
            st.success("Manual props cleared. Refresh board.")
        c_refresh_note.info("After adding or clearing, hit Refresh / Load Board.")

        st.markdown("""
        <div class="warn-card">
        <b>Important:</b> Manual props are still real lines only if you enter them from a real source. They do not change the projection DB or learning baseline.
        </div>
        """, unsafe_allow_html=True)


    with tab_manual:
        st.subheader("Manual Line Adjuster")
        st.caption("This changes only the betting line used for Edge/Pick/EV/Rating. It does NOT change projections or learning baselines.")

        inv_market = {v: k for k, v in MARKET_MAP.items()}
        manual_rows = load_manual_lines()
        if manual_rows:
            st.write("Active manual line overrides")
            st.dataframe(pd.DataFrame(manual_rows.values()), use_container_width=True, height=220)
        else:
            st.info("No manual line overrides active.")

        with st.form("manual_line_form"):
            m_player = st.text_input("Player name", value="")
            m_market_label = st.selectbox("Market to adjust", list(MARKET_MAP.values()), key="manual_market_select")
            m_book = st.text_input("Book optional — leave blank to apply to all books", value="")
            m_line = st.number_input("Manual line", min_value=0.0, max_value=150.0, step=0.5)
            m_note = st.text_input("Note optional", value="")
            c1, c2 = st.columns(2)
            save_manual = c1.form_submit_button("Save manual line")
            clear_manual = c2.form_submit_button("Clear manual line")

            if save_manual:
                if not m_player.strip():
                    st.warning("Enter a player name.")
                else:
                    key = set_manual_line_override(m_player.strip(), inv_market[m_market_label], m_line, m_book.strip(), m_note.strip())
                    st.success(f"Saved manual line override: {key}. Refresh board to apply.")
            if clear_manual:
                if not m_player.strip():
                    st.warning("Enter a player name.")
                else:
                    ok = clear_manual_line_override(m_player.strip(), inv_market[m_market_label], m_book.strip())
                    if ok:
                        st.success("Manual line override cleared. Refresh board to apply.")
                    else:
                        st.info("No matching manual override found.")

        st.markdown("""
        <div class="warn-card">
        <b>Important:</b> Manual lines are for checking another book/Underdog-style line against your projection.
        They do not overwrite the sportsbook line from The Odds API and do not train the model.
        </div>
        """, unsafe_allow_html=True)


    with tab_stats:
        st.subheader("Projection database")
        st.caption("Upload a CSV to improve projections. Columns: player, points, rebounds, assists, threes, steals, blocks, pace, dvp")
        current_db = projection_db_combined()
        db_rows = []
        for player, stats in current_db.items():
            row = {"player": player}; row.update(stats); db_rows.append(row)
        st.dataframe(pd.DataFrame(db_rows), use_container_width=True, height=360)
        upload = st.file_uploader("Upload projection CSV", type=["csv"])
        if upload is not None:
            try:
                up = pd.read_csv(upload)
                if "player" not in up.columns:
                    st.error("CSV must include a 'player' column.")
                else:
                    custom = {}
                    for _, r in up.iterrows():
                        p = str(r.get("player", "")).strip()
                        if not p: continue
                        custom[p] = {
                            "points": safe_float(r.get("points"), safe_float(r.get("avg_pts"), 0)) or 0,
                            "rebounds": safe_float(r.get("rebounds"), safe_float(r.get("avg_reb"), 0)) or 0,
                            "assists": safe_float(r.get("assists"), safe_float(r.get("avg_ast"), 0)) or 0,
                            "threes": safe_float(r.get("threes"), safe_float(r.get("avg_3pm"), 0)) or 0,
                            "steals": safe_float(r.get("steals"), safe_float(r.get("avg_stl"), 0)) or 0,
                            "blocks": safe_float(r.get("blocks"), safe_float(r.get("avg_blk"), 0)) or 0,
                            "pace": safe_float(r.get("pace"), safe_float(r.get("pace_factor"), 1.0)) or 1.0,
                            "dvp": safe_float(r.get("dvp"), safe_float(r.get("dvp_adjustment"), 1.0)) or 1.0,
                        }
                    save_custom_projection_db(custom)
                    st.success(f"Saved custom projection DB for {len(custom)} players. Refresh board to apply.")
            except Exception as e:
                st.error(f"Could not read CSV: {e}")

    with tab_logs:
        req_rows = load_json(REQUEST_LOG_FILE, [])
        if isinstance(req_rows, list) and req_rows:
            st.dataframe(pd.DataFrame(req_rows).tail(200), use_container_width=True, height=500)
        else:
            st.caption("No request logs yet.")
else:
    tab_games, tab_manual_props_empty, tab_logs = st.tabs(["📅 Games", "➕ Manual Props", "🧾 Logs"])
    with tab_games:
        render_game_cards(events)

    with tab_manual_props_empty:
        st.subheader("Manual Prop Board")
        st.caption("Games are loading but player props are not. Enter real lines manually from Underdog or another book.")

        inv_market_manual = {v: k for k, v in MARKET_MAP.items()}
        current_manual = load_manual_props()
        if current_manual:
            st.dataframe(pd.DataFrame(current_manual), use_container_width=True, height=260)
        else:
            st.info("No manual props added yet.")

        with st.form("manual_prop_add_form_empty"):
            mp_player = st.text_input("Player", value="", placeholder="Jackie Young")
            mp_market_label = st.selectbox("Market", list(MARKET_MAP.values()), key="manual_prop_market_empty")
            mp_line = st.number_input("Line", min_value=0.0, max_value=150.0, step=0.5, value=15.5, key="manual_prop_line_empty")
            mp_book = st.text_input("Book / Source", value="Underdog", key="manual_prop_book_empty")
            mp_matchup = st.text_input("Matchup optional", value="Manual Entry", key="manual_prop_match_empty")
            mp_day = st.selectbox("Game day label", ["Manual", "Today", "Tomorrow"], index=0, key="manual_prop_day_empty")
            c_ov, c_un = st.columns(2)
            mp_over_price = c_ov.number_input("Over price", value=-110, step=1, key="manual_over_empty")
            mp_under_price = c_un.number_input("Under price", value=-110, step=1, key="manual_under_empty")
            mp_note = st.text_input("Note optional", value="", key="manual_prop_note_empty")
            submitted_manual_prop = st.form_submit_button("Add manual prop to board")

            if submitted_manual_prop:
                if not mp_player.strip():
                    st.warning("Enter a player name.")
                else:
                    add_manual_prop(mp_player.strip(), inv_market_manual[mp_market_label], mp_line, mp_book.strip(), mp_matchup.strip(), mp_day, mp_over_price, mp_under_price, mp_note.strip())
                    st.success("Manual prop added. Hit Refresh / Load Board to show it on player cards.")

        if st.button("Clear ALL manual props", use_container_width=True, key="clear_manual_props_empty"):
            clear_manual_props()
            st.success("Manual props cleared. Refresh board.")


    with tab_logs:
        req_rows = load_json(REQUEST_LOG_FILE, [])
        if isinstance(req_rows, list) and req_rows:
            st.dataframe(pd.DataFrame(req_rows).tail(200), use_container_width=True, height=500)
        else:
            st.caption("No request logs yet.")
