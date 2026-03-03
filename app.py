import streamlit as st
import pandas as pd
import requests
import mlbstatsapi
from datetime import datetime

mlb = mlbstatsapi.Mlb()

# --- THE DEEP-MATCH ODDS ENGINE ---
def get_real_odds(home_team, away_team, api_key):
    """Fuzzy matching to catch National Teams and Split Squads."""
    if not api_key: return 0.0
    
    url = f"https://api.the-odds-api.com/v4/sports/baseball_mlb/odds/?apiKey={api_key}&regions=us&markets=totals"
    
    try:
        response = requests.get(url).json()
        # Clean the team names for better matching
        h_clean = home_team.lower().replace("national team", "").strip()
        a_clean = away_team.lower().replace("national team", "").strip()

        for game in response:
            g_home = game['home_team'].lower()
            g_away = game['away_team'].lower()
            
            # Check if home or away team name exists ANYWHERE in the odds string
            if h_clean[:5] in g_home or a_clean[:5] in g_away or h_clean[:5] in g_away:
                # Return the total from the first available bookmaker
                return float(game['bookmakers'][0]['markets'][0]['outcomes'][0]['point'])
    except Exception as e:
        return 0.0
    return 0.0

# --- THE PREDICTION LOGIC ---
def get_ai_prediction(vegas_line, home_team, away_team, venue):
    if vegas_line <= 0: return None, 0.0
    
    adj = 0.0
    # Arizona Park Factor (Higher scores in dry air)
    if any(p in venue for p in ["Salt River", "Sloan", "Camelback", "Surprise"]):
        adj += 0.8
    
    # WBC Offense Factor (USA/DR/Venezuela have All-Star lineups)
    power_nations = ["United States", "Dominican Republic", "Venezuela", "Japan"]
    if home_team in power_nations or away_team in power_nations:
        adj += 1.2

    proj = round((vegas_line + adj) * 2) / 2
    edge = proj - vegas_line
    return proj, edge

# --- UI RENDER ---
st.title("⚾ MLB Intelligence Pro: WBC Exhibition Edition")
api_key = st.sidebar.text_input("Odds API Key", type="password")

schedule = mlb.get_scheduled_games_by_date(date="2026-03-03")

for game in schedule:
    home = game.teams.home.team.name
    away = game.teams.away.team.name
    venue = game.venue.name
    
    # 1. New Fuzzy Match Fetch
    vegas_line = get_real_odds(home, away, api_key)
    
    # 2. Get AI Prediction
    ai_proj, edge = get_ai_prediction(vegas_line, home, away, venue)

    with st.expander(f"🔥 {away} @ {home}"):
        if vegas_line == 0.0:
            st.error(f"⚠️ Feed Sync Error: Sportsbook has '{home}' but API is using a different name string.")
            st.info("Manual Entry Override: If you see the line, enter it in the sidebar to force the AI logic.")
        else:
            c1, c2, c3 = st.columns(3)
            c1.metric("Vegas Line", vegas_line)
            c2.metric("AI Projection", ai_proj, delta=f"{edge:+.1f}")
            
            if edge >= 1.0:
                c3.success("🎯 TAKE OVER")
            elif edge <= -1.0:
                c3.error("🎯 TAKE UNDER")
            else:
                c3.info("PASS")
