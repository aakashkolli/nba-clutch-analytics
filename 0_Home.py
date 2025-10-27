import streamlit as st
import pandas as pd
from modules.utils import (
    set_page_config, 
    inject_custom_css, 
    load_data, 
    get_season_data, 
    METRIC_NAME_MAP,
    initialize_session_state
)

set_page_config()
inject_custom_css()
initialize_session_state()

player_df, team_df = load_data()
if player_df is None:
    st.stop()

player_df_season, team_df_season, selected_season = get_season_data(player_df, team_df)

st.title("NBA Clutch Analytics Dashboard")
st.markdown(f"### Analyzing Player and Team Performance Under Pressure for the **{selected_season}** Season")

st.markdown("""
This dashboard provides an in-depth look at how NBA players and teams perform in "clutch" situations. 
It moves beyond simple box scores to uncover who truly rises to the occasion when the game is on the line.
""")

st.subheader("Key Features")
st.page_link("pages/1_Player_Profile.py", label="**Player Profile:** Deep-dive into a single player's clutch vs. non-clutch stats.", icon="👤")
st.page_link("pages/2_Team_Profile.py", label="**Team Profile:** Analyze a team's win rate and top performers in close games.", icon="👥")
st.page_link("pages/3_Player_Comparison.py", label="**Player Comparison:** Compare two players head-to-head on clutch performance.", icon="📊")
st.page_link("pages/4_Scenario_Simulator.py", label="**Scenario Simulator:** Model the 'what-if' impact of increased player usage.", icon="⚙️")
st.page_link("pages/5_Predictive_Model.py", label="**Predictive Model:** Forecast next season's top clutch players using a machine learning model.", icon="🤖")

st.markdown("---")
st.header(f"Top 15 Clutch Players ({selected_season})")
st.markdown(f"Ranked by the **{METRIC_NAME_MAP['CPI']}**, a composite metric measuring performance in high-pressure games (minimum 5 clutch games played for full calculation).")

top_players = player_df_season[player_df_season['GP_clutch'] >= 5].nlargest(15, 'CPI')

display_cols = {
    'PLAYER_NAME': 'Player',
    'TEAM_NAME': 'Team',
    'CPI': 'CPI',
    'GP_clutch': 'Clutch GP',
    'PPG_clutch': 'Clutch PPG',
    'FG_PCT_clutch': 'Clutch FG%',
    'FG_PCT_diff': 'FG% Differential'
}

top_players_display = top_players[display_cols.keys()].rename(columns=display_cols)

st.dataframe(
    top_players_display.style
        .format({
            'CPI': '{:.3f}', 
            'Clutch FG%': '{:.1%}', 
            'FG% Differential': '{:+.1%}'
        })
        .background_gradient(cmap='Greens', subset=['CPI'])
        .background_gradient(cmap='RdYlGn', subset=['FG% Differential'], vmin=-0.1, vmax=0.1)
        .set_properties(**{'text-align': 'left'}),
    width='stretch'
)