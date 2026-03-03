import streamlit as st
import requests
import mlbstatsapi
from datetime import datetime

mlb = mlbstatsapi.Mlb()

# --- THE AGGRESSIVE AUTO-MATCH ENGINE ---
def get_auto_vegas_line(home_team, away_team, api_key):
    """Automatically finds the line by matching keywords across feeds."""
    if not api_key: return 0.0
    
    url = f"https://api.the-odds-api.com/v4/sports/baseball_mlb/odds/?apiKey={api_key}&regions=us&markets=totals"
    
    try:
        response = requests.get(url).json()
        
        # We look for the "Core Name" (e.g., 'Guardians' or 'Dodgers')
        h_core = home_team.split(' ')[-1].lower()
        a_core = away_team.split(' ')[-1].lower()

        for game in response:
            g_home = game['home_team'].lower()
            g_away = game['away_team'].lower()
            
            # Check if the core names exist in the sportsbook's team strings
            if h_core in g_home or a_core in g_away or a_core in g_home or h_core in g_away:
                # Pull the first available point total
                for book in game.get('bookmakers', []):
                    for market in book.get('markets', []):
                        if market['key'] == 'totals':
                            return float(market['outcomes'][0]['point'])
    except:
        return 0.0
    return 0.0

# --- MAIN DASHBOARD ---
st.title("⚾ MLB Intelligence: Live 2026 Feed")
api_key = st.sidebar.text_input("Odds API Key", type="password")

# Fetch Today's MLB Schedule
today = datetime.now().strftime("%Y-%m-%d")
schedule = mlb.get_scheduled_games_by_date(date=today)

# Block list for non-MLB teams (WBC)
wbc_keywords = ["Cuba", "Nicaragua", "Panama", "Israel", "Canada", "Brazil", "Netherlands", "States", "Dominican"]

if schedule:
    for game in schedule:
        home = game.teams.home.team.name
        away = game.teams.away.team.name
        venue = game.venue.name

        # 1. REMOVE NON-MLB GAMES
        if any(word in home or word in away for word in wbc_keywords):
            continue

        # 2. AUTOMATIC LINE FETCH
        vegas_line = get_auto_vegas_line(home, away, api_key)

        # 3. AI PROJECTION LOGIC
        # Park Factors for March 3rd (Cactus League dry air boost)
        park_adj = 0.8 if any(p in venue for p in ["Goodyear", "Camelback", "Peoria", "Sloan"]) else 0.0
        
        # ABS Challenge Edge (High success teams = Longer innings)
        abs_adj = 0.4 if "Dodgers" in home or "Padres" in away or "Athletics" in home else 0.0

        if vegas_line > 0:
            ai_proj = round((vegas_line + park_adj + abs_adj) * 2) / 2
            edge = round(ai_proj - vegas_line, 1)

            with st.expander(f"🏟️ {away} @ {home}"):
                c1, c2, c3 = st.columns(3)
                c1.metric("Vegas Line", vegas_line)
                c2.metric("AI Projection", ai_proj, delta=f"{edge:+.1f}")
                
                if edge >= 0.5:
                    c3.success("🎯 TAKE OVER")
                elif edge <= -0.5:
                    c3.error("🎯 TAKE UNDER")
                else:
                    c3.info("NO EDGE")
        else:
            # This only shows if the API key is missing or the game is literally not on the board
            st.sidebar.error(f"Missing Line: {away} @ {home}")
