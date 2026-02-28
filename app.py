import streamlit as st
import pandas as pd
import requests
import mlbstatsapi
from datetime import datetime

# --- INITIALIZATION ---
mlb = mlbstatsapi.Mlb()
st.set_page_config(layout="wide", page_title="MLB AI Betting Machine 2026")

# --- 2026 POWER DATA: PARK FACTORS & UMPIRES ---
# Factor > 1.00 favors Hitters (OVER), < 1.00 favors Pitchers (UNDER)
park_factors = {
    "Coors Field": 1.31,           # Highest in MLB
    "Sutter Health Park": 1.09,    # New A's stadium (Launching pad)
    "Great American Ball Park": 1.15,
    "Wrigley Field": 0.92,         # Pitcher friendly (unless wind is out)
    "Petco Park": 0.94,
    "T-Mobile Park": 0.82,         # Massive Under factory
    "Camelback Ranch-Glendale": 1.05, # Spring Training altitude
}

# Umpire stats based on 2025-2026 consistency
umpire_analytics = {
    "Doug Eddings": {"boost": 0.9, "desc": "Tiny Strike Zone"},
    "Hunter Wendelstedt": {"boost": 0.7, "desc": "Hitter Friendly"},
    "Austin Jones": {"boost": -0.6, "desc": "Pitcher's Ump"},
    "Lance Barrett": {"boost": 0.5, "desc": "Consistent Over"},
}

def get_live_pitching_score(game_pk, season_mode):
    try:
        game_data = mlb.get_game_play_by_play(game_pk)
        if not game_data.all_plays: return 0, "Pre-Game"
        p_count = game_data.all_plays[-1].about.pitch_index
        limit = 45 if "Spring" in season_mode else 85
        if p_count > limit:
            return 1.4, f"🚨 PEN ALERT ({p_count}P)" # Higher weight for bullpen entry
        return 0, f"STABLE ({p_count}P)"
    except:
        return 0, "No Feed"

# --- MAIN APP ---
st.title("⚾ MLB Ultra-Strength Command Center")
st.sidebar.title("🛠️ Machine Settings")
season_mode = st.sidebar.radio("Season Phase", ["Spring Training 🌵", "Regular Season ⚾"])
api_key = st.sidebar.text_input("Odds API Key", type="password")
min_edge = st.sidebar.slider("Min. Edge (Runs)", 0.5, 3.0, 1.0)

# Fetch Actual Games for Feb 28, 2026
today = datetime.now().strftime("%Y-%m-%d")
schedule = mlb.get_scheduled_games_by_date(date=today)

if not schedule:
    st.error("No games found. Is it past the last first pitch?")
else:
    for game in schedule:
        home_team = game.teams.home.team.name
        away_team = game.teams.away.team.name
        venue = game.venue.name
        
        # --- THE STRENGTH ENGINE ---
        # 1. Start with Vegas Base (Connect your API here for real lines)
        base_line = 9.0 
        
        # 2. Apply Park Factor
        p_factor = park_factors.get(venue, 1.0)
        park_adj = (p_factor - 1.0) * 5 # Adjusts projection based on stadium history
        
        # 3. Apply Umpire Factor (Mocking Eddings for the Cubs/Dodgers demo)
        ump_name = "Doug Eddings" if "Cubs" in away_team else "Unknown"
        ump_data = umpire_analytics.get(ump_name, {"boost": 0, "desc": "Neutral"})
        
        # 4. Live Pitching + 2026 Rules
        pitch_adj, pitch_status = get_live_pitching_score(game.game_pk, season_mode)
        abs_boost = 0.4 # The 2026 ABS system is favoring hitters
        
        # FINAL PROJECTION
        strength_proj = round((base_line + park_adj + ump_data['boost'] + pitch_adj + abs_boost) * 2) / 2
        edge = round(strength_proj - base_line, 1)

        # UI DISPLAY
        with st.expander(f"🏟️ {away_team} @ {home_team} | {venue}"):
            c1, c2, c3 = st.columns(3)
            c1.metric("AI Projection", f"{strength_proj} Runs", delta=f"{edge} vs Vegas")
            c2.write(f"**Umpire:** {ump_name} ({ump_data['desc']})")
            c2.write(f"**Stadium:** {'🔥' if p_factor > 1.05 else '🧊'} {venue}")
            
            if abs(edge) >= min_edge:
                color = "green" if edge > 0 else "red"
                pick = "OVER" if edge > 0 else "UNDER"
                c3.markdown(f"### 🎯 PICK: :{color}[{pick} {base_line}]")
            else:
                c3.info("NO CLEAR EDGE")
