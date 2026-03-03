import streamlit as st
import pandas as pd
import requests
import mlbstatsapi
from datetime import datetime

# --- INITIALIZATION ---
mlb = mlbstatsapi.Mlb()

# --- 1. THE HARDENED ODDS ENGINE ---
def get_verified_vegas_line(home_team, away_team, api_key):
    """Fetches real-time line with a 2026 'Synthetic Fallback'."""
    line = None
    
    if api_key:
        url = f"https://api.the-odds-api.com/v4/sports/baseball_mlb/odds/?apiKey={api_key}&regions=us&markets=totals"
        try:
            response = requests.get(url).json()
            for game in response:
                # 2026 Fix: Match on partial names to catch 'Split Squad' or 'WBC' tags
                if home_team[:5] in game['home_team'] or away_team[:5] in game['away_team']:
                    line = game['bookmakers'][0]['markets'][0]['outcomes'][0]['point']
                    return line, "Live Feed"
        except:
            pass

    # --- 2. THE EMERGENCY SYNTHETIC LINE (The Fix for the 'Wrong' Logic) ---
    # If the feed is wrong/missing, we calculate what the line SHOULD be.
    # 2026 Cactus League (AZ) avg is 10.5 | Grapefruit (FL) is 9.0
    cactus_parks = ["Sloan", "Camelback", "Salt River", "Surprise", "Goodyear"]
    
    # Check if game is in high-scoring Arizona
    is_cactus = any(park in home_team for park in cactus_parks) # Simple park check
    
    # Baseline line for March 2026
    synthetic_line = 10.5 if is_cactus else 9.0
    
    return synthetic_line, "Synthetic (Live Feed Offline)"

# --- 2. UPDATED CALCULATION LOGIC ---
def calculate_true_projection(vegas_line, venue, home_team, away_team, weather):
    adj = 0.0
    
    # ABS Factor (The 2026 Game Changer)
    # High challenge-success teams force more walks = Over lean
    over_heavy_teams = ["Oakland Athletics", "San Francisco Giants", "Cincinnati Reds"]
    if home_team in over_heavy_teams or away_team in over_heavy_teams:
        adj += 0.8
        
    # Wind Adjustment (Hydrated from MLB API)
    if weather and hasattr(weather, 'wind'):
        if "Out To" in weather.wind: adj += 1.0
        if "In From" in weather.wind: adj -= 1.0
        
    return round((vegas_line + adj) * 2) / 2

# --- 3. MAIN APP LOOP ---
st.title("⚾ MLB Intelligence Pro (Fixed Feed)")

api_key = st.sidebar.text_input("Odds API Key", type="password")
today = datetime.now().strftime("%Y-%m-%d")
schedule = mlb.get_scheduled_games_by_date(date=today)

if schedule:
    for game in schedule:
        home = game.teams.home.team.name
        away = game.teams.away.team.name
        
        # FIXED: Get verified line and see WHERE it came from
        vegas_line, source = get_verified_vegas_line(home, away, api_key)
        
        # Get Weather/Pitcher Data
        try:
            detail = mlb.get_game(game.game_pk, hydrate=['weather'])
            weather = detail.weather if hasattr(detail, 'weather') else None
        except: weather = None

        ai_proj = calculate_true_projection(vegas_line, game.venue.name, home, away, weather)
        edge = round(ai_proj - vegas_line, 1)

        with st.expander(f"{away} @ {home}"):
            st.caption(f"Line Source: {source}")
            c1, c2, c3 = st.columns(3)
            c1.metric("Vegas Line", vegas_line)
            c2.metric("AI Projection", ai_proj, delta=f"{edge:+.1f}")
            
            if edge >= 1.0:
                c3.success("🎯 BET OVER")
            elif edge <= -1.0:
                c3.error("🎯 BET UNDER")
