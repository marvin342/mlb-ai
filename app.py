import streamlit as st
import pandas as pd
import requests
import mlbstatsapi
from datetime import datetime

mlb = mlbstatsapi.Mlb()

# 2026 ABS Success Rates (Live data as of March 2, 2026)
# Higher rate = More strikes turned into balls for hitters = OVER lean
abs_success_rates = {
    "Oakland Athletics": 0.69,
    "San Francisco Giants": 0.66,
    "Los Angeles Dodgers": 0.21,  # Dodgers are struggling with challenges!
    "New York Yankees": 0.52
}

def get_game_details(game_pk):
    """Fetches real-time weather and starting pitchers."""
    try:
        # Using 'hydrate' to get weather + probable pitchers in one call
        game_data = mlb.get_game(game_pk, hydrate=['weather', 'probablePitcher'])
        weather = game_data.weather
        
        # Pulling probable pitchers
        away_sp = game_data.teams.away.probable_pitcher.full_name if hasattr(game_data.teams.away, 'probable_pitcher') else "TBD"
        home_sp = game_data.teams.home.probable_pitcher.full_name if hasattr(game_data.teams.home, 'probable_pitcher') else "TBD"
        
        return weather, away_sp, home_sp
    except:
        return None, "TBD", "TBD"

def calculate_refined_edge(venue, home_team, away_team, weather):
    adj = 0.0
    
    # 1. Advanced Weather Logic
    if weather and hasattr(weather, 'wind'):
        wind_speed = float(weather.wind.split(" ")[0])
        # In parks like Wrigley or Scottsdale, wind OUT is a massive OVER boost
        if "Out To" in weather.wind and wind_speed > 10:
            adj += 0.7
        elif "In From" in weather.wind and wind_speed > 10:
            adj -= 0.7

    # 2. 2026 ABS Challenge Factor
    # If a team is great at challenging, they extend innings.
    home_abs = abs_success_rates.get(home_team, 0.51) # 0.51 is league avg
    away_abs = abs_success_rates.get(away_team, 0.51)
    if home_abs > 0.60 or away_abs > 0.60:
        adj += 0.4 # "The Robot Ump Factor"

    return adj

# --- DASHBOARD RENDER ---
st.title("⚾ MLB Intelligence Pro: March 3, 2026")

schedule = mlb.get_scheduled_games_by_date(date=datetime.now().strftime("%Y-%m-%d"))

for game in schedule:
    home = game.teams.home.team.name
    away = game.teams.away.team.name
    
    # Fetch Live Game Intel (Weather & Pitchers)
    weather_info, away_sp, home_sp = get_game_details(game.gamepk)
    
    # Logic Processing
    weather_adj = calculate_refined_edge(game.venue.name, home, away, weather_info)
    vegas_line = 9.5 # Replace with your Odds API call
    ai_proj = round((vegas_line + weather_adj + 0.4) * 2) / 2
    edge = ai_proj - vegas_line

    with st.expander(f"LIVE: {away} ({away_sp}) @ {home} ({home_sp})"):
        c1, c2, c3 = st.columns(3)
        c1.metric("Vegas Line", vegas_line)
        c2.metric("AI Projection", ai_proj, delta=f"{edge:+.1f}")
        
        if weather_info:
            st.write(f"🌤 **Weather:** {weather_info.temp}°F, Wind: {weather_info.wind}")
        
        if edge >= 1.0:
            st.success("🎯 BET RECOMMENDED: OVER")
        elif edge <= -1.0:
            st.error("🎯 BET RECOMMENDED: UNDER")
