import streamlit as st
import pandas as pd
from modules.utils import (
    set_page_config, 
    inject_custom_css, 
    load_data, 
    get_season_data, 
    METRIC_NAME_MAP,
    generate_comparison_report_html
)
from modules.visualizations import plot_player_kpis
from modules.analytics import get_player_profile

set_page_config()
inject_custom_css()

player_df, team_df = load_data()
if player_df is None:
    st.stop()

player_df_season, team_df_season, selected_season = get_season_data(player_df, team_df)

st.header("Player Clutch Comparison")
st.markdown(f"Compare two players head-to-head on their **{selected_season}** clutch performance.")

player_list = sorted(player_df_season['PLAYER_NAME'].unique())

# Default to LeBron James and another star player for interesting comparison
default_p1_index = 0
default_p2_index = 1

if 'LeBron James' in player_list:
    default_p1_index = player_list.index('LeBron James')
    notable_players = ['Stephen Curry', 'Kevin Durant', 'Giannis Antetokounmpo', 'Kawhi Leonard', 'Chris Paul']
    for notable in notable_players:
        if notable in player_list and notable != 'LeBron James':
            default_p2_index = player_list.index(notable)
            break
    else:
        default_p2_index = 1 if len(player_list) > 1 else 0

col1, col2 = st.columns(2)
with col1:
    p1_name = st.selectbox("Select Player 1", player_list, index=default_p1_index)
with col2:
    p2_name = st.selectbox("Select Player 2", player_list, index=default_p2_index)

p1_data = get_player_profile(player_df_season, p1_name, selected_season)
p2_data = get_player_profile(player_df_season, p2_name, selected_season)

if p1_data is None or p2_data is None:
    st.warning("Please select two valid players.")
    st.stop()

st.markdown("---")
st.subheader("Performance KPIs (Clutch vs. Non-Clutch)")

st.markdown(f"**<span style='color:#1D428A;'>■ {p1_name}</span>** (Bar) vs. **<span style='color:#6C6D6F;'>| {p1_name}'s Non-Clutch</span>** (Line)", unsafe_allow_html=True)
st.markdown(f"**<span style='color:#C8102E;'>■ {p2_name}</span>** (Bar) vs. **<span style='color:#6C6D6F;'>| {p2_name}'s Non-Clutch</span>** (Line)", unsafe_allow_html=True)

fig_compare = plot_player_kpis(p1_data, compare_data=p2_data)
st.plotly_chart(fig_compare, use_container_width=True)

st.markdown("---")
st.subheader("Statistical Head-to-Head")

metrics_to_compare = [
    'CPI', 'GP_clutch', 'PPG_clutch', 'FG_PCT_clutch', 'FG_PCT_diff',
    'AST_TO_RATIO_clutch', 'PLUS_MINUS_PER_GAME_clutch'
]
p1_stats = p1_data[metrics_to_compare]
p2_stats = p2_data[metrics_to_compare]

compare_df = pd.DataFrame([p1_stats, p2_stats], index=[p1_name, p2_name]).T
compare_df = compare_df.rename_axis("Metric").reset_index()
compare_df['Metric'] = compare_df['Metric'].map(METRIC_NAME_MAP).fillna(compare_df['Metric'])

st.dataframe(
    compare_df.style.format({p1_name: '{:.3f}', p2_name: '{:.3f}'}),
    width='stretch',
    hide_index=True
)

st.markdown("---")

col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    st.subheader("Download Comparison Report")
with col2:
    st.write("")
with col3:
    report_html = generate_comparison_report_html(p1_data, p2_data, selected_season)
    st.download_button(
        label="📄 Download Report",
        data=report_html,
        file_name=f"{p1_name.replace(' ', '_')}_vs_{p2_name.replace(' ', '_')}_comparison_{selected_season}.html",
        mime="text/html",
        use_container_width=True
    )