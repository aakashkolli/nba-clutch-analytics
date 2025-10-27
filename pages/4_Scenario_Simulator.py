import streamlit as st
import pandas as pd
from modules.utils import (
    set_page_config, 
    inject_custom_css, 
    load_data, 
    get_season_data
)
from modules.visualizations import plot_simulation_results
from modules.analytics import get_player_profile, run_simulation

set_page_config()
inject_custom_css()

player_df, team_df = load_data()
if player_df is None:
    st.stop()

player_df_season, team_df_season, selected_season = get_season_data(player_df, team_df)

st.header("Scenario Simulator")
st.markdown("What if a player took more shots in clutch situations? This tool simulates the potential impact on their key stats.")

player_list = sorted(player_df_season['PLAYER_NAME'].unique())

default_index = 0
if 'LeBron James' in player_list:
    default_index = player_list.index('LeBron James')

selected_player = st.selectbox("Select Player", player_list, index=default_index)

player_data = get_player_profile(player_df_season, selected_player, selected_season)

if player_data is None:
    st.warning(f"No data available for {selected_player} in {selected_season}.")
else:
    st.subheader(f"Simulate for {selected_player}")
    
    shot_increase = st.slider(
        "Increase in Clutch Field Goal Attempts (FGA) %",
        min_value=-50,
        max_value=100,
        value=10,
        step=5,
        help="Simulate a % change in the player's FGA per game in clutch situations."
    )
    
    old_stats, new_stats = run_simulation(player_data, shot_increase)
    
    st.subheader("Simulation Results")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Simulated PPG", f"{new_stats['PPG']:.2f}", f"{new_stats['PPG'] - old_stats['PPG']:.2f}")
    col2.metric("Simulated FGA/Game", f"{new_stats['FGA_per_game']:.2f}", f"{new_stats['FGA_per_game'] - old_stats['FGA_per_game']:.2f}")
    col3.metric("Simulated TOPG", f"{new_stats['TOPG']:.2f}", f"{new_stats['TOPG'] - old_stats['TOPG']:.2f}")
    col4.metric("Simulated AST/TO", f"{new_stats['AST/TO']:.2f}", f"{new_stats['AST/TO'] - old_stats['AST/TO']:.2f}")

    fig_sim = plot_simulation_results(old_stats, new_stats)
    st.plotly_chart(fig_sim, use_container_width=True)
    
    st.markdown("---")
    st.info(f"""
    **Simulation Logic:**
    * Assumes player's **Points-per-FGA** rate remains constant.
    * Calculates new Points based on the additional {shot_increase}% shot attempts.
    * Estimates a corresponding increase in turnovers based on the player's turnover-per-shot rate, with a small elasticity factor for increased usage.
    * Assists per game are held constant.
    """)