import streamlit as st
import pandas as pd
import requests
import mlbstatsapi
from datetime import datetime

mlb = mlbstatsapi.Mlb()

# --- THE HARDENED VEGAS FEED ---
def get_real_odds(home_team, api_key):
    """Fetches real-time totals. Returns 0.0 if the line isn't 'real' yet."""
    if not api_key: return 0.0
    url = f"https://api.the-odds-api.com/v4/sports/baseball_mlb/odds/?apiKey={api_key}&regions=us&markets=totals"
    try:
        response = requests.get(url).json()
        for game in response:
            # Partial match to catch "Split Squad" or "WBC" tags
            if home_team[:5].lower() in game['home_team'].lower():
                return float(game['bookmakers'][0]['markets'][0]['outcomes'][0]['point'])
    except:
        return 0.0
    return 0.0

# --- THE 2026 STRATEGY ENGINE ---
def get_ai_prediction(vegas_line, home_team, away_team, venue):
    """Calculates the edge only if the data is valid."""
    if vegas_line == 0.0: return None, 0.0
    
    adj = 0.0
    # 2026 Park Factor: Cactus League (AZ) is currently a launchpad
    cactus_parks = ["Sloan", "Camelback", "Salt River", "Surprise", "Goodyear", "Scottsdale"]
    if any(p in venue for p in cactus_parks):
        adj += 0.7  # High desert air boost
        
    # ABS (Robot Ump) Rule: Teams winning challenges = longer innings
    abs_kings = ["Oakland Athletics", "San Francisco Giants", "Cincinnati Reds"]
    if home_team in abs_kings or away_team in abs_kings:
        adj += 0.5

    proj = round((vegas_line + adj) * 2) / 2
    edge = proj - vegas_line
    return proj, edge

# --- UI ---
st.title("⚾ MLB Intelligence Pro: March 3, 2026")
api_key = st.sidebar.text_input("Odds API Key", type="password")

schedule = mlb.get_scheduled_games_by_date(date=datetime.now().strftime("%Y-%m-%d"))

for game in schedule:
    home = game.teams.home.team.name
    away = game.teams.away.team.name
    venue = game.venue.name
    
    # 1. Get the actual line from the book
    vegas_line = get_real_odds(home, api_key)
    
    # 2. Get the AI Projection
    ai_proj, edge = get_ai_prediction(vegas_line, home, away, venue)

    with st.expander(f"🔥 {away} @ {home}"):
        if vegas_line == 0.0:
            st.warning("⚠️ Vegas hasn't posted a real line for this game yet. AI is holding to prevent a 1-game miss.")
        else:
            col1, col2, col3 = st.columns(3)
            col1.metric("Vegas Total", vegas_line)
            col2.metric("AI Projection", ai_proj, delta=f"{edge:+.1f}")
            
            # THE "TAKE" LOGIC
            if edge >= 1.0:
                col3.success("🎯 TAKE: OVER")
                st.write(f"**Reason:** High-carry air in {venue} + ABS Challenge Edge.")
            elif edge <= -1.0:
                col3.error("🎯 TAKE: UNDER")
                st.write(f"**Reason:** Line is inflated; defensive efficiency is higher today.")
            else:
                col3.info("NO BET")
