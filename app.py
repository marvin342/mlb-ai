import streamlit as st
import pandas as pd
import requests
import mlbstatsapi
from datetime import datetime

mlb = mlbstatsapi.Mlb()

# --- 1. TEAM NAME MAPPING (The "Translation" Table) ---
# This ensures "Kingdom of the Netherlands" in MLB API matches "Netherlands" in Odds API
team_map = {
    "Kingdom of the Netherlands": "Netherlands",
    "United States": "USA",
    "Dominican Republic": "Dominican Republic",
    "Great Britain": "Great Britain",
    "Oakland Athletics": "Oakland Athletics", # Or "Oakland A's"
    "Tampa Bay Rays": "Tampa Bay Rays",
    "Minnesota Twins": "Minnesota Twins"
}

# --- 2. THE IMPROVED ODDS FETCH ---
def get_live_vegas_line(home_team, away_team, api_key):
    if not api_key: return 0.0
    url = f"https://api.the-odds-api.com/v4/sports/baseball_mlb/odds/?apiKey={api_key}&regions=us&markets=totals"
    try:
        response = requests.get(url).json()
        # Get mapped names
        h_target = team_map.get(home_team, home_team).lower()
        a_target = team_map.get(away_team, away_team).lower()

        for game in response:
            g_home = game['home_team'].lower()
            g_away = game['away_team'].lower()
            
            # Match if mapped name is in the odds string
            if h_target[:6] in g_home or a_target[:6] in g_away:
                return float(game['bookmakers'][0]['markets'][0]['outcomes'][0]['point'])
    except:
        return 0.0
    return 0.0

# --- 3. MAIN UI & SIDEBAR ---
st.title("⚾ MLB AI Pro: March 3, 2026")

with st.sidebar:
    st.header("Settings")
    api_key = st.text_input("Odds API Key", type="password")
    manual_line = st.number_input("Manual Line Override (Optional)", min_value=0.0, max_value=20.0, value=0.0, step=0.5)
    st.info("If the live feed fails, type the Vegas line above to see the AI pick.")

# Get Games
schedule = mlb.get_scheduled_games_by_date(date="2026-03-03")

for game in schedule:
    home = game.teams.home.team.name
    away = game.teams.away.team.name
    venue = game.venue.name
    
    # Use Manual Override if provided, otherwise fetch live
    vegas_line = manual_line if manual_line > 0 else get_live_vegas_line(home, away, api_key)
    
    # AI Logic (2026 ABS + Park Factor)
    adj = 0.0
    if any(p in venue for p in ["Sloan", "Camelback", "Salt River", "Surprise"]): adj += 0.8
    if "USA" in home or "United States" in home or "Dominican" in home: adj += 1.2
    
    ai_proj = round((vegas_line + adj) * 2) / 2 if vegas_line > 0 else 0
    edge = round(ai_proj - vegas_line, 1)

    with st.expander(f"🔥 {away} @ {home}"):
        if vegas_line == 0:
            st.warning("Feed Mismatch. Please use the 'Manual Line Override' in the sidebar.")
        else:
            c1, c2, c3 = st.columns(3)
            c1.metric("Vegas Line", vegas_line)
            c2.metric("AI Projection", ai_proj, delta=f"{edge:+.1f}")
            
            # Explicit Take Logic
            if edge >= 1.0:
                c3.success("🎯 TAKE OVER")
            elif edge <= -1.0:
                c3.error("🎯 TAKE UNDER")
            else:
                c3.info("PASS")
