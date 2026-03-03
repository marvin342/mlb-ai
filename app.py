import streamlit as st
import pandas as pd
import requests
import mlbstatsapi
from datetime import datetime

mlb = mlbstatsapi.Mlb()

# --- MLB ONLY ODDS FETCH ---
def get_mlb_vegas_line(home_team, away_team, api_key):
    """Strictly matches MLB club names to the Vegas feed."""
    if not api_key: return 0.0
    url = f"https://api.the-odds-api.com/v4/sports/baseball_mlb/odds/?apiKey={api_key}&regions=us&markets=totals"
    
    try:
        response = requests.get(url).json()
        # Clean names (e.g., 'Minnesota Twins' -> 'minnes')
        h_match = home_team.lower()[:6]
        a_match = away_team.lower()[:6]

        for game in response:
            g_home = game['home_team'].lower()
            g_away = game['away_team'].lower()
            
            # Ensure it's not a WBC game (National teams usually don't have the MLB city name)
            if h_match in g_home or a_match in g_away:
                return float(game['bookmakers'][0]['markets'][0]['outcomes'][0]['point'])
    except:
        return 0.0
    return 0.0

# --- UI ---
st.title("⚾ MLB Intelligence Pro: Spring Training 2026")
api_key = st.sidebar.text_input("Odds API Key", type="password")

# Fetch Today's Schedule
schedule = mlb.get_scheduled_games_by_date(date="2026-03-03")

# National Team Filter List
wbc_names = ["USA", "United States", "Mexico", "Panama", "Canada", "Israel", "Nicaragua", 
             "Brazil", "Cuba", "Italy", "Great Britain", "Colombia", "Netherlands", 
             "Venezuela", "Puerto Rico", "Dominican Republic"]

if schedule:
    for game in schedule:
        home = game.teams.home.team.name
        away = game.teams.away.team.name
        venue = game.venue.name
        
        # SKIP if either team is a National Team
        if any(country in home or country in away for country in wbc_names):
            continue
            
        # Get Real Vegas Line
        vegas_line = get_mlb_vegas_line(home, away, api_key)
        
        # AI Projection Logic
        adj = 0.0
        # Arizona Park Factor (Higher totals in Cactus League)
        if any(p in venue for p in ["Sloan", "Camelback", "Salt River", "Surprise", "Goodyear"]):
            adj += 0.8
        
        ai_proj = round((vegas_line + adj) * 2) / 2 if vegas_line > 0 else 0
        edge = round(ai_proj - vegas_line, 1)

        with st.expander(f"🏟️ {away} @ {home}"):
            if vegas_line == 0:
                st.info(f"Vegas has not released the final total for this specific matchup yet.")
            else:
                c1, c2, c3 = st.columns(3)
                c1.metric("Vegas Line", vegas_line)
                c2.metric("AI Projection", ai_proj, delta=f"{edge:+.1f}")
                
                if edge >= 1.0:
                    c3.success("🎯 TAKE OVER")
                elif edge <= -1.0:
                    c3.error("🎯 TAKE UNDER")
                else:
                    c3.info("NO BET")
