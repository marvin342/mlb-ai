import streamlit as st
import pandas as pd
from datetime import datetime
import mlbstatsapi

mlb = mlbstatsapi.Mlb()

# --- 2026 LIVE DATA: ABS SUCCESS RATES (Updated Mar 3, 2026) ---
# Percentage of ball/strike challenges WON. 
# High win rate = Extended innings = Lean OVER.
team_abs_stats = {
    "Oakland Athletics": 0.69, "San Francisco Giants": 0.66, "Cincinnati Reds": 0.61,
    "Miami Marlins": 0.61, "San Diego Padres": 0.61, "Minnesota Twins": 0.58,
    "Colorado Rockies": 0.55, "Boston Red Sox": 0.55, "New York Yankees": 0.52,
    "Detroit Tigers": 0.46, "Texas Rangers": 0.38, "New York Mets": 0.35,
    "Baltimore Orioles": 0.25, "Los Angeles Dodgers": 0.21
    # Teams not listed default to League Avg: 0.51
}

# --- PARK & LEAGUE FACTORS ---
cactus_parks = [
    "Salt River Fields", "Sloan Park", "Camelback Ranch", "Goodyear Ballpark",
    "Surprise Stadium", "Tempe Diablo Stadium", "Hohokam Stadium", 
    "Peoria Sports Complex", "Scottsdale Stadium", "American Family Fields"
]

def get_projection_logic(home_team, away_team, venue, weather):
    adj = 0.0
    
    # 1. Park Factor (Drier Arizona air = Higher Exit Velocity)
    if any(park in venue for park in cactus_parks):
        adj += 0.5 
    
    # 2. 2026 ABS Challenge Edge
    # If both teams are good at challenging (e.g., A's vs Giants), the Over is highly likely.
    home_rate = team_abs_stats.get(home_team, 0.51)
    away_rate = team_abs_stats.get(away_team, 0.51)
    if home_rate > 0.60 and away_rate > 0.60:
        adj += 0.8
    elif home_rate < 0.30 and away_rate < 0.30:
        adj -= 0.6

    # 3. Weather (Wind is the 2026 MVP)
    if weather and hasattr(weather, 'wind'):
        if "Out To" in weather.wind: adj += 0.6
        if "In From" in weather.wind: adj -= 0.6
        
    return adj

# --- DASHBOARD UI ---
st.title("⚾ MLB AI Pro: March 3, 2026")
st.subheader("Spring Training Intelligence Dashboard")

today = datetime.now().strftime("%Y-%m-%d")
schedule = mlb.get_scheduled_games_by_date(date=today)

if not schedule:
    st.info("No games currently live. Check back at 1:05 PM MST.")
else:
    for game in schedule:
        # Hydrate weather and pitcher data
        detail = mlb.get_game(game.gamepk, hydrate=['weather', 'probablePitcher'])
        home = game.teams.home.team.name
        away = game.teams.away.team.name
        venue = game.venue.name
        
        # Calculations
        weather = detail.weather if hasattr(detail, 'weather') else None
        edge_adj = get_projection_logic(home, away, venue, weather)
        
        # Display
        with st.expander(f"🌵 {away} @ {home} - {venue}"):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**ABS Success:** {away} ({team_abs_stats.get(away, 0.51):.0%}) | {home} ({team_abs_stats.get(home, 0.51):.0%})")
                if weather:
                    st.write(f"🌡 {weather.temp}°F | 🌬 {weather.wind}")
            
            with col2:
                if edge_adj >= 0.7:
                    st.success(f"🔥 STRONG OVER BIAS (+{edge_adj})")
                elif edge_adj <= -0.7:
                    st.error(f"❄️ STRONG UNDER BIAS ({edge_adj})")
                else:
                    st.info("Neutral Projection")
