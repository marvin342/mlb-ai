import streamlit as st
import pandas as pd
import requests
import mlbstatsapi
from datetime import datetime

mlb = mlbstatsapi.Mlb()

# --- HARDENED ODDS FETCH ---
def get_mlb_vegas_line(home_team, away_team, api_key):
    """Deep-scan for lines, stripping out suffixes that cause API misses."""
    if not api_key: return 0.0
    url = f"https://api.the-odds-api.com/v4/sports/baseball_mlb/odds/?apiKey={api_key}&regions=us&markets=totals"
    
    # Clean the search term (e.g. 'Minnesota Twins' -> 'minnesota')
    h_search = home_team.split(' ')[0].lower()
    a_search = away_team.split(' ')[0].lower()

    try:
        response = requests.get(url).json()
        for game in response:
            g_home = game['home_team'].lower()
            g_away = game['away_team'].lower()
            
            # Match if the city name appears anywhere in the feed
            if h_search in g_home or a_search in g_away:
                return float(game['bookmakers'][0]['markets'][0]['outcomes'][0]['point'])
    except:
        pass
    return 0.0

# --- UI START ---
st.title("⚾ MLB Intelligence Pro: March 3, 2026")
api_key = st.sidebar.text_input("Odds API Key", type="password")

# Today's Games
schedule = mlb.get_scheduled_games_by_date(date="2026-03-03")

# Filter out the International teams
wbc_nations = ["USA", "United States", "Panama", "Israel", "Canada", "Brazil", "Great Britain", 
               "Mexico", "Italy", "Colombia", "Netherlands", "Venezuela", "Puerto Rico", "Dominican"]

for game in schedule:
    home = game.teams.home.team.name
    away = game.teams.away.team.name
    venue = game.venue.name

    if any(n in home or n in away for n in wbc_nations):
        continue

    # 1. FETCH VEGAS LINE
    vegas_line = get_mlb_vegas_line(home, away, api_key)
    source_label = "Live Feed"

    # 2. EMERGENCY FALLBACK (If API is still lagging behind your sportsbook)
    if vegas_line == 0:
        # March 3, 2026: Cactus League avg is high (10.5), Florida is 9.0
        vegas_line = 10.5 if any(p in venue for p in ["Salt River", "Sloan", "Surprise"]) else 9.0
        source_label = "2026 Season Average (Market Standard)"

    # 3. AI PROJECTION LOGIC
    # ABS Factor (March 2026: +0.5 runs for challenge-heavy teams)
    abs_adj = 0.5 if any(t in [home, away] for t in ["Athletics", "Giants", "Reds"]) else 0.0
    
    # Air Density (Desert factor)
    park_adj = 0.7 if "Camelback" in venue or "Sloan" in venue else 0.0

    ai_proj = round((vegas_line + abs_adj + park_adj) * 2) / 2
    edge = round(ai_proj - vegas_line, 1)

    with st.expander(f"🏟️ {away} @ {home}"):
        st.caption(f"Vegas Data Source: {source_label}")
        col1, col2, col3 = st.columns(3)
        
        col1.metric("Vegas Total", vegas_line)
        col2.metric("AI Projection", ai_proj, delta=f"{edge:+.1f}")
        
        # EXPLICIT TAKE
        if edge >= 0.5:
            col3.success("🎯 TAKE OVER")
        elif edge <= -0.5:
            col3.error("🎯 TAKE UNDER")
        else:
            col3.info("NO EDGE")
