import streamlit as st
import pandas as pd
from modules.utils import (
    set_page_config, 
    inject_custom_css, 
    load_data, 
    get_season_data,
    METRIC_NAME_MAP
)
from modules.visualizations import plot_team_win_pct

set_page_config()
inject_custom_css()

player_df, team_df = load_data()
if player_df is None:
    st.stop()

player_df_season, team_df_season, selected_season = get_season_data(player_df, team_df)

st.header("Team Clutch Profile")
st.markdown("Analyze how teams perform in clutch-game situations.")

if team_df_season.empty:
    st.warning(f"No team data available for {selected_season}.")
else:
    team_list = sorted(team_df_season['TEAM_NAME'].unique())
    selected_team = st.selectbox("Select Team", team_list)
    
    team_data = team_df_season[team_df_season['TEAM_NAME'] == selected_team].iloc[0]
    
    st.subheader(f"{selected_team} - {selected_season}")
    
    col1, col2, col3 = st.columns(3)
    col1.metric(
        "Clutch Win %",
        f"{team_data['WIN_PCT_clutch']:.1%}",
        f"{team_data['WIN_PCT_clutch'] - team_data['WIN_PCT_non_clutch']:.1%} vs. Non-Clutch"
    )
    col2.metric("Clutch Games", f"{int(team_data['GP_clutch'])}", f"{int(team_data['WINS_clutch'])} W - {int(team_data['GP_clutch'] - team_data['WINS_clutch'])} L")
    col3.metric("Non-Clutch Games", f"{int(team_data['GP_non_clutch'])}", f"{int(team_data['WINS_non_clutch'])} W - {int(team_data['GP_non_clutch'] - team_data['WINS_non_clutch'])} L")
    
    fig_team = plot_team_win_pct(team_data)
    st.plotly_chart(fig_team, use_container_width=True)
    
    st.markdown("---")
    
    st.subheader(f"Top 5 Clutch Players for {selected_team} (min. 5 clutch GP)")
    team_players = player_df_season[
        (player_df_season['TEAM_NAME'] == selected_team) &
        (player_df_season['GP_clutch'] >= 5)
    ].nlargest(5, 'CPI')
    
    display_cols = {
        'PLAYER_NAME': 'Player',
        'CPI': 'CPI',
        'GP_clutch': 'Clutch GP',
        'PPG_clutch': 'Clutch PPG',
        'FG_PCT_clutch': 'Clutch FG%',
        'FG_PCT_diff': 'FG% Differential'
    }
    team_players_display = team_players[display_cols.keys()].rename(columns=display_cols)

    st.dataframe(
        team_players_display.style
            .format({'CPI': '{:.3f}', 'Clutch FG%': '{:.1%}', 'FG% Differential': '{:+.1%}'})
            .background_gradient(cmap='Greens', subset=['CPI']),
        width='stretch'
    )