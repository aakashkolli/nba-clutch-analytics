import streamlit as st
import pandas as pd
from modules.utils import (
    set_page_config, 
    inject_custom_css, 
    load_data, 
    get_season_data, 
    METRIC_NAME_MAP,
    initialize_session_state,
    generate_player_report_html
)
from modules.visualizations import plot_player_kpis, plot_league_distribution
from modules.analytics import get_player_profile

set_page_config()
inject_custom_css()
initialize_session_state()

player_df, team_df = load_data()
if player_df is None:
    st.stop()

player_df_season, team_df_season, selected_season = get_season_data(player_df, team_df)
st.sidebar.markdown("---")
st.sidebar.subheader("Favorite Players")

for fav_player in st.session_state.favorites:
    if st.sidebar.button(f"Remove {fav_player}", key=f"fav_{fav_player}", width='stretch'):
        st.session_state.favorites.remove(fav_player)
        st.rerun()

st.header("Player Clutch Profile")
st.markdown("Compare a player's clutch vs. non-clutch performance and see how they stack up against the league.")

player_list = sorted(player_df_season['PLAYER_NAME'].unique())

# Priority: favorites → LeBron James → first alphabetically
default_player = None
default_index = 0

if st.session_state.favorites:
    player_list = st.session_state.favorites + [p for p in player_list if p not in st.session_state.favorites]
    default_player = st.session_state.favorites[0]
    default_index = 0
elif 'LeBron James' in player_list:
    default_player = 'LeBron James'
    default_index = player_list.index('LeBron James')
else:
    default_player = player_list[0]
    default_index = 0

selected_player = st.selectbox("Select Player", player_list, index=default_index)

player_data = get_player_profile(player_df_season, selected_player, selected_season)

if player_data is None:
    st.warning(f"No data available for {selected_player} in {selected_season}.")
else:
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader(f"{selected_player} ({player_data['TEAM_NAME']}) - {selected_season}")
    with col2:
        if selected_player not in st.session_state.favorites:
            if st.button(f"Add {selected_player} to Favorites", width='stretch'):
                st.session_state.favorites.append(selected_player)
                st.rerun()
        else:
            st.success("⭐ Favorite Player")

    fig_kpi = plot_player_kpis(player_data)
    st.plotly_chart(fig_kpi, use_container_width=True)
    
    st.markdown("---")
    
    st.subheader("League Comparison (min. 10 clutch GP)")
    
    df_for_ranking = player_df_season[player_df_season['GP_clutch'] >= 10].copy()
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        metric_list = ['CPI', 'PPG_clutch', 'FG_PCT_clutch', 'FG_PCT_diff', 'AST_TO_RATIO_clutch']
        selected_metric = st.selectbox("Select Metric", metric_list, format_func=lambda x: METRIC_NAME_MAP[x])
        
        df_for_ranking['Rank'] = df_for_ranking[selected_metric].rank(ascending=False, method='min')
        
        player_rank_series = df_for_ranking[df_for_ranking['PLAYER_NAME'] == selected_player]['Rank']
        
        if not player_rank_series.empty:
            player_rank = player_rank_series.values[0]
            total_players = len(df_for_ranking)
            st.metric(
                label=f"League Rank",
                value=f"#{int(player_rank)}",
                delta=f"of {total_players} players",
                delta_color="off"
            )
        else:
            st.warning("Player does not meet min. 10 clutch GP for ranking.")
        
        st.markdown("---")
        
        report_html = generate_player_report_html(player_data, selected_season, df_for_ranking, selected_metric)
        st.download_button(
            label="📄 Download Report",
            data=report_html,
            file_name=f"{selected_player.replace(' ', '_')}_clutch_report_{selected_season}.html",
            mime="text/html",
            use_container_width=True
        )

    with col2:
        fig_dist = plot_league_distribution(df_for_ranking, player_data, selected_metric)
        st.plotly_chart(fig_dist, use_container_width=True)