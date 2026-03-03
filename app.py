import streamlit as st
import pandas as pd
import requests
import mlbstatsapi
from datetime import datetime

# --- INITIALIZATION ---
mlb = mlbstatsapi.Mlb()
st.set_page_config(layout="wide", page_title="MLB AI 2026")

# --- 2026 LIVE DATA: ABS SUCCESS RATES (Updated Mar 3, 2026) ---
# High rate = More strikes turned to balls = Favor OVER
team_abs_stats = {
    "Oakland Athletics": 0.69, "San Francisco Giants": 0.66, "Cincinnati Reds": 0.61,
    "Miami Marlins": 0.61, "San Diego Padres": 0.61, "Minnesota Twins": 0.58,
    "Colorado Rockies": 0.55, "Boston Red Sox": 0.55, "New York Yankees": 0.52,
    "Detroit Tigers": 0.46, "Texas Rangers": 0.38, "New York Mets": 0.35,
    "Baltimore Orioles": 0.25, "Los Angeles Dodgers": 0.21
}

# --- PARK FACTORS ---
cactus_parks = [
    "Salt River Fields", "Sloan Park", "Camelback Ranch", "Goodyear Ballpark",
    "Surprise Stadium", "Tempe Diablo Stadium", "Hohokam Stadium", 
    "Peoria Sports Complex", "Scottsdale Stadium", "American Family Fields"
]

# --- CORE FUNCTIONS ---
def get_live_vegas_line(home_team, api_key):
    """Fetches real-time Over/Under line."""
    if not api_key: return 9.5
    url = f"https://api.the-odds-api.com/v4/sports/baseball_mlb/odds/?apiKey={api_key}&regions=us&markets=totals"
    try:
        response = requests.get(url).json()
        for game in response:
            if home_team in game['home_team']:
                return game['bookmakers'][0]['markets'][0]['outcomes'][0]['point']
    except:
        return 9.5
    return 9.5

def calculate_projection(home_team, away_team, venue, weather):
    """Main 2026 Logic Engine."""
    adj = 0.0
    
    # 1. Park Factor (Cactus League / Desert Air)
    if any(park in venue for park in cactus_parks):
        adj += 0.6 
    
    # 2. 2026 ABS Challenge Edge
    home_rate = team_abs_stats.get(home_team, 0.51)
    away_rate = team_abs_stats.get(away_team, 0.51)
    if home_rate > 0.60 or away_rate > 0.60:
        adj += 0.5
        
    # 3. Weather Hydration
    if weather and hasattr(weather, 'wind'):
        if "Out To" in weather.wind: adj += 0.7
        if "In From" in weather.wind: adj -= 0.7
        
    return adj

# --- MAIN DASHBOARD ---
st.title("⚾ MLB Intelligence Pro: March 3, 2026")

# Get Today's Schedule
today = datetime.now().strftime("%Y-%m-%d")
schedule = mlb.get_scheduled_games_by_date(date=today)

api_key = st.sidebar.text_input("Odds API Key", type="password")
st.sidebar.info("Tip: A's and Giants are the 'Over' kings due to ABS challenges.")

if not schedule:
    st.warning("No games found for this date.")
else:
    for game in schedule:
        # FIX: Using game_pk (snake_case) to avoid the AttributeError
        game_id = game.game_pk
        
        # Hydrate Data Safely
        try:
            detail = mlb.get_game(game_id, hydrate=['weather', 'probablePitcher', 'linescore'])
            weather = detail.weather if hasattr(detail, 'weather') else None
            
            # Get Scores
            home_score = detail.live_data.linescore.teams.home.runs if hasattr(detail.live_data, 'linescore') else 0
            away_score = detail.live_data.linescore.teams.away.runs if hasattr(detail.live_data, 'linescore') else 0
            status = game.status.detailed_state
            
            # Get Pitchers
            away_sp = detail.teams.away.probable_pitcher.full_name if hasattr(detail.teams.away, 'probable_pitcher') else "TBD"
            home_sp = detail.teams.home.probable_pitcher.full_name if hasattr(detail.teams.home, 'probable_pitcher') else "TBD"
        except:
            weather, home_score, away_score, status = None, 0, 0, "Scheduled"
            away_sp, home_sp = "TBD", "TBD"

        home_name = game.teams.home.team.name
        away_name = game.teams.away.team.name
        venue = game.venue.name

        # Calculate Edge
        vegas_line = get_live_vegas_line(home_name, api_key)
        logic_adj = calculate_projection(home_name, away_name, venue, weather)
        ai_proj = round((vegas_line + logic_adj + 0.4) * 2) / 2
        edge = round(ai_proj - vegas_line, 1)

        # RENDER UI
        with st.expander(f"{status}: {away_name} ({away_sp}) @ {home_name} ({home_sp})"):
            if status == "In Progress":
                st.subheader(f"LIVE SCORE: {away_name} {away_score} - {home_name} {home_score}")
                
            c1, c2, c3 = st.columns(3)
            c1.metric("Vegas Line", vegas_line)
            c2.metric("AI Projection", ai_proj, delta=f"{edge:+.1f}")
            
            if edge >= 1.0:
                c3.success("✅ STRONG OVER")
            elif edge <= -1.0:
                c3.error("✅ STRONG UNDER")
            else:
                c3.info("No Edge")

            if weather:
                st.write(f"🌤 **Weather:** {weather.temp}°F | **Wind:** {weather.wind}")
