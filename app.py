import streamlit as st
import pandas as pd
import requests
import mlbstatsapi
from datetime import datetime

# --- INITIALIZATION ---
mlb = mlbstatsapi.Mlb()
st.set_page_config(layout="wide", page_title="MLB AI 2026")

# --- 2026 LIVE ODDS ENGINE ---
def get_live_vegas_line(home_team, api_key):
    """Fetches the actual Over/Under line from the sportsbook."""
    if not api_key: return 9.5  # Fallback
    
    url = f"https://api.the-odds-api.com/v4/sports/baseball_mlb/odds/?apiKey={api_key}&regions=us&markets=totals"
    try:
        response = requests.get(url).json()
        # Find the specific game by home team name
        for game in response:
            if home_team in game['home_team']:
                return game['bookmakers'][0]['markets'][0]['outcomes'][0]['point']
    except:
        return 9.5
    return 9.5

# --- SPRING TRAINING VOLATILITY MODEL ---
def calculate_spring_strength(venue_name, away_team):
    """Adjusts projection based on 2026 Spring-specific factors."""
    adj = 0.0
    
    # 1. Park Factors (Arizona 'Cactus' air is thinner/drier = More Runs)
    cactus_league_parks = ["Camelback Ranch", "Sloan Park", "Surprise Stadium", "Goodyear Ballpark"]
    if any(park in venue_name for park in cactus_league_parks):
        adj += 0.6  # Boost for desert carry
        
    # 2. Split Squad (SS) Dilution
    # If a team is split up, the lineup is weaker = Fewer Runs (Under Lean)
    if "SS" in away_team or "Split Squad" in away_team:
        adj -= 0.8
        
    return adj

# --- MAIN DASHBOARD ---
st.title("⚾ MLB Intelligence: Feb 28, 2026")

# Get Today's Real Schedule
today = datetime.now().strftime("%Y-%m-%d")
schedule = mlb.get_scheduled_games_by_date(date=today)

# Sidebar for Key
api_key = st.sidebar.text_input("Odds API Key", type="password")

if not schedule:
    st.warning("No games found for this date.")
else:
    for game in schedule:
        home = game.teams.home.team.name
        away = game.teams.away.team.name
        venue = game.venue.name
        
        # 1. Fetch the REAL line for THIS specific match
        vegas_line = get_live_vegas_line(home, api_key)
        
        # 2. Apply the "Strength" Logic
        spring_adj = calculate_spring_strength(venue, away)
        abs_tax = 0.4 # 2026 ABS rule boost
        
        # 3. Final Calculation
        ai_proj = round((vegas_line + spring_adj + abs_tax) * 2) / 2
        edge = round(ai_proj - vegas_line, 1)

        # RENDER
        with st.expander(f"🔥 {away} @ {home}"):
            col1, col2, col3 = st.columns(3)
            col1.metric("Vegas Line", vegas_line)
            col2.metric("AI Projection", ai_proj, delta=edge)
            
            # Recommendation Logic
            if edge >= 1.0:
                col3.success(f"✅ STRONG OVER {vegas_line}")
                st.write(f"*Reasoning: High-carry air at {venue} + ABS Challenge Favoring Hitters.*")
            elif edge <= -1.0:
                col3.error(f"✅ STRONG UNDER {vegas_line}")
                st.write(f"*Reasoning: Split-squad lineup detected. Defensive value high.*")
            else:
                col3.info("Hold: No Significant Edge")
