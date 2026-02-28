import streamlit as st
import pandas as pd
import requests
import mlbstatsapi

# --- INITIALIZATION ---
mlb = mlbstatsapi.Mlb()
st.set_page_config(layout="wide", page_title="MLB AI Betting Machine")

# --- DATA: STADIUMS & UMPIRES (Carried over) ---
stadium_data = {
    "Wrigley Field": {"angle": 45, "roof": "Open"},
    "Fenway Park": {"angle": 70, "roof": "Open"},
    "Coors Field": {"angle": 20, "roof": "Open"},
    "Chase Field": {"angle": 0, "roof": "Retractable"} # etc...
}

umpire_db = {
    "Doug Eddings": {"edge": 0.8, "trend": "OVER"},
    "Andy Fletcher": {"edge": 0.7, "trend": "OVER"},
    "Austin Jones": {"edge": -0.6, "trend": "UNDER"}
}

# --- NEW: LIVE PITCH COUNT TRACKER ---
def get_live_pitching_status(game_pk):
    """Checks if the starter is hitting the 'Danger Zone' for an Over."""
    try:
        # Pull live play-by-play data from MLB API
        game_data = mlb.get_game_play_by_play(game_pk)
        current_pitcher_count = game_data.all_plays[-1].about.pitch_index if game_data.all_plays else 0
        
        # Spring Training Logic: Managers pull at ~50 pitches
        if current_pitcher_count > 45:
            return 1.1, f"⚠️ STARTER AT {current_pitcher_count} PITCHES (BULLPEN SOON)"
        return 0, "✅ Starter Stable"
    except:
        return 0, "Live Data Pending"

# --- LOGIC: WEATHER & ABS CHALLENGE (2026 Rules) ---
def calculate_weather_adjustment(wind_speed, wind_deg, stadium_name):
    # (Same logic as before: Wind Out = +1.2, Wind In = -0.8)
    return 0.5 # Example return for demo

# --- UI: SIDEBAR & SEASON TOGGLE ---
st.sidebar.title("💰 Machine Settings")
season_mode = st.sidebar.radio("Current Phase", ["Spring Training 🌵", "Regular Season ⚾"])
api_key = st.sidebar.text_input("Odds API Key", type="password")
min_edge = st.sidebar.slider("Min. Run Edge to Bet", 0.3, 2.0, 0.7)

# --- MAIN DASHBOARD ---
st.title("⚾ MLB Over/Under Command Center")
st.write(f"System Mode: **{season_mode}** | Date: **Feb 28, 2026**")

col1, col2 = st.columns([3, 1])

with col1:
    st.subheader("🔥 Live Projections")
    
    # Example Game Data (In production, map game_pk from schedule)
    active_games = [
        {"home": "Chicago Cubs", "away": "Milwaukee Brewers", "line": 8.5, "venue": "Wrigley Field", "pk": 715000}
    ]

    for game in active_games:
        vegas_line = game['line']
        
        # 1. Umpire Factor
        ump_factor = umpire_db.get("Doug Eddings", {}).get('edge', 0)
        
        # 2. Weather Factor
        weather_factor = calculate_weather_adjustment(12, 180, game['venue'])
        
        # 3. NEW: Live Pitch Factor (The 'Bullpen Burn')
        pitch_factor, pitch_label = get_live_pitching_status(game['pk'])
        
        # 4. Final AI Projection (Adjusted for Season Phase)
        # Spring Training has higher variance (+0.5 base)
        base_variance = 0.5 if "Spring" in season_mode else 0.0
        ai_proj = round((vegas_line + ump_factor + weather_factor + pitch_factor + base_variance) * 2) / 2
        edge = round(ai_proj - vegas_line, 1)
        
        with st.expander(f"{game['away']} @ {game['home']} | Line: {vegas_line}"):
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Vegas Line", f"{vegas_line}")
            c2.metric("AI Total", f"{ai_proj}", delta=edge)
            
            c3.write(f"**Umpire:** {ump_factor:+}")
            c3.write(f"**Pitch Status:** {pitch_label}")
            
            if edge >= min_edge:
                c4.success(f"🎯 BET OVER {vegas_line}")
            elif edge <= -min_edge:
                c4.error(f"🎯 BET UNDER {vegas_line}")
            else:
                c4.info("NO VALUE")

with col2:
    st.subheader("🚨 2026 Market Alerts")
    st.warning("⚡ ABS CHALLENGES: Hitters winning 54% of strike-zone challenges today. (Leans OVER)")
    st.info("📊 SPRING TREND: Road teams using 'B-Squad' lineups (Leans UNDER).")
