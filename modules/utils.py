import streamlit as st
import pandas as pd
import os

# constants
PLAYER_DATA_PATH = 'data/processed/player_performance.csv'
TEAM_DATA_PATH = 'data/processed/team_performance.csv'

# Human-readable names for dataset column names
METRIC_NAME_MAP = {
    'CPI': 'Clutch Player Index (CPI)',
    'PPG_clutch': 'Clutch Points Per Game',
    'FG_PCT_clutch': 'Clutch Field Goal %',
    'FG3_PCT_clutch': 'Clutch 3-Point %',
    'AST_TO_RATIO_clutch': 'Clutch Assist/Turnover Ratio',
    'PLUS_MINUS_PER_GAME_clutch': 'Clutch Plus-Minus Per Game',
    'PPG_diff': 'PPG Differential (Clutch vs. Non-Clutch)',
    'FG_PCT_diff': 'FG% Differential (Clutch vs. Non-Clutch)',
}

# --- Data Loading ---
@st.cache_data
def load_data():
    """
    Loads and caches the processed player and team data.
    """
    if not os.path.exists(PLAYER_DATA_PATH) or not os.path.exists(TEAM_DATA_PATH):
        st.error(f"Processed data not found! Please run `python modules/data_loader.py` first from your terminal.")
        return None, None
        
    player_df = pd.read_csv(PLAYER_DATA_PATH)
    team_df = pd.read_csv(TEAM_DATA_PATH)
    
    # Post-load cleaning - CPI should never be NaN with new calculation method
    player_df['CPI'] = pd.to_numeric(player_df['CPI'], errors='coerce')
    # Filter out players with 0 clutch games for a cleaner UI
    player_df = player_df[player_df['GP_clutch'] > 0].copy()
    
    return player_df, team_df

# --- Page Setup and Styling ---
def set_page_config():
    """
    Sets the page configuration and injects custom NBA-themed CSS.
    """
    st.set_page_config(
        page_title="NBA Clutch Analytics",
        layout="wide"
    )

def inject_custom_css():
    """
    Injects custom CSS for a dark theme with high contrast.
    """
    css = """
    <style>
        /* --- Top Navigation Bar --- */
        header[data-testid="stHeader"] {
            background-color: #000000 !important;
            height: 3rem !important;
        }
        
        header[data-testid="stHeader"] * {
            color: #FFFFFF !important;
        }
        
        /* Deploy button and menu */
        header[data-testid="stHeader"] button {
            background-color: #1D428A !important;
            color: #FFFFFF !important;
            border: 1px solid #FFFFFF !important;
        }
        
        header[data-testid="stHeader"] button:hover {
            background-color: #FFFFFF !important;
            color: #000000 !important;
        }
        
        /* Three dots menu */
        header[data-testid="stHeader"] svg {
            fill: #FFFFFF !important;
        }
        
        /* --- Base Theme - BLACK BACKGROUND --- */
        .stApp {
            background-color: #000000 !important;
            color: #FFFFFF !important;
        }
        
        /* Main content */
        .main .block-container {
            background-color: #000000 !important;
            color: #FFFFFF !important;
        }
        
        /* Headers */
        h1, h2, h3, h4, h5, h6 {
            font-weight: 700 !important;
            color: #FFFFFF !important;
        }
        
        /* Regular text */
        .main p, .main span:not([data-baseweb]), .main div:not([data-baseweb]) {
            color: #FFFFFF !important;
        }
        
        /* All text elements */
        p, span, div, label {
            color: #FFFFFF !important;
        }
        
        /* --- Sidebar --- */
        .stSidebar {
            background-color: #1A1A1A !important;
            border-right: 1px solid #333333 !important;
        }
        
        .stSidebar > div {
            background-color: #1A1A1A !important;
        }
        
        .stSidebar * {
            color: #FFFFFF !important;
        }
        
        .stSidebar h1, .stSidebar h2, .stSidebar h3 {
            color: #FFFFFF !important;
            font-weight: 700 !important;
        }
        
        .stSidebar label, .stSidebar span, .stSidebar p {
            color: #FFFFFF !important;
        }
        
        /* Sidebar navigation links */
        .stSidebar .stPageLink-NavLink {
            color: #FFFFFF !important;
            background-color: transparent !important;
        }
        
        .stSidebar .stPageLink-NavLink:hover {
            color: #FFFFFF !important;
            background-color: #333333 !important;
        }
        
        /* --- Dropdowns and Controls --- */
        .stSelectbox div[data-baseweb="select"] {
            background-color: #333333 !important;
            border: 1px solid #555555 !important;
            color: #FFFFFF !important;
        }
        
        .stSelectbox div[data-baseweb="select"] > div {
            background-color: #333333 !important;
            color: #FFFFFF !important;
        }
        
        .stSelectbox div[data-baseweb="select"] span {
            color: #FFFFFF !important;
        }
        
        .stSelectbox div[data-baseweb="select"] * {
            color: #FFFFFF !important;
        }
        
        .stSelectbox label {
            color: #FFFFFF !important;
        }
        
        /* Dropdown arrow */
        .stSelectbox div[data-baseweb="select"] svg {
            fill: #FFFFFF !important;
        }
        
        /* Dropdown menu styling */
        div[data-baseweb="popover"] {
            background-color: #333333 !important;
        }
        
        div[data-baseweb="popover"] div[role="listbox"] {
            background-color: #333333 !important;
        }
        
        div[data-baseweb="popover"] ul {
            background-color: #333333 !important;
        }
        
        div[data-baseweb="popover"] li {
            background-color: #333333 !important;
            color: #FFFFFF !important;
        }
        
        div[data-baseweb="popover"] li * {
            color: #FFFFFF !important;
        }
        
        div[data-baseweb="popover"] li:hover {
            background-color: #555555 !important;
            color: #FFFFFF !important;
        }
        
        div[data-baseweb="popover"] li:hover * {
            color: #FFFFFF !important;
        
        /* --- Buttons --- */
        .stButton button {
            background-color: #1D428A !important;
            color: #FFFFFF !important;
            font-weight: 700 !important;
            border: none !important;
            border-radius: 5px !important;
            padding: 8px 16px !important;
        }
        
        .stButton button:hover {
            background-color: #333333 !important;
            color: #FFFFFF !important;
        }
        
        /* Download buttons */
        .stDownloadButton button {
            background-color: #28a745 !important;
            color: #FFFFFF !important;
            font-weight: 700 !important;
            border: none !important;
            border-radius: 5px !important;
            padding: 8px 16px !important;
        }
        
        .stDownloadButton button:hover {
            background-color: #218838 !important;
            color: #FFFFFF !important;
        }
        
        /* --- Metric Cards --- */
        div[data-testid="metric-container"] {
            background-color: #1A1A1A !important;
            border: 1px solid #333333 !important;
            border-radius: 8px !important;
            padding: 16px !important;
            color: #FFFFFF !important;
        }
        
        div[data-testid="metric-container"] * {
            color: #FFFFFF !important;
        }
        
        /* --- Dataframes --- */
        .stDataFrame {
            background-color: #1A1A1A !important;
            border: 1px solid #333333 !important;
            border-radius: 8px !important;
            color: #FFFFFF !important;
        }
        
        .stDataFrame * {
            color: #FFFFFF !important;
        }
        
        /* Dataframe headers */
        .stDataFrame thead tr th {
            background-color: #333333 !important;
            color: #FFFFFF !important;
        }
        
        /* Dataframe rows */
        .stDataFrame tbody tr td {
            background-color: #1A1A1A !important;
            color: #FFFFFF !important;
        }
        
        /* --- Plotly Charts --- */
        .stPlotlyChart {
            background-color: #1A1A1A !important;
        }
        
        /* --- Links --- */
        .stPageLink-NavLink {
            color: #66B2FF !important;
            text-decoration: none !important;
        }
        
        .stPageLink-NavLink:hover {
            color: #FFFFFF !important;
        }
        
        /* --- Markdown content --- */
        .stMarkdown {
            color: #FFFFFF !important;
        }
        
        .stMarkdown * {
            color: #FFFFFF !important;
        }
        
        /* --- Sliders --- */
        .stSlider > div > div > div > div {
            background-color: #333333 !important;
        }
        
        .stSlider label {
            color: #FFFFFF !important;
        }
        
        /* --- Text Input --- */
        .stTextInput > div > div > input {
            background-color: #333333 !important;
            color: #FFFFFF !important;
            border: 1px solid #555555 !important;
        }
        
        .stTextInput label {
            color: #FFFFFF !important;
        }
        
        /* --- Warnings and Info --- */
        .stAlert {
            background-color: #1A1A1A !important;
            border: 1px solid #555555 !important;
            color: #FFFFFF !important;
        }
        
        .stAlert * {
            color: #FFFFFF !important;
        }

    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

def get_season_data(player_df, team_df):
    """
    Gets unique seasons and displays the season selector in the sidebar.
    Returns the filtered dataframes for the selected season.
    """
    
    st.sidebar.title("NBA Clutch Analytics")
    
    seasons = sorted(player_df['SEASON'].unique(), reverse=True)
    selected_season = st.sidebar.selectbox("Select Season", seasons)
    
    player_df_season = player_df[player_df['SEASON'] == selected_season].copy()
    team_df_season = team_df[team_df['SEASON'] == selected_season].copy()
    
    return player_df_season, team_df_season, selected_season

def initialize_session_state():
    """Initializes session state variables if they don't exist."""
    if 'favorites' not in st.session_state:
        st.session_state.favorites = []

def get_default_player_index(player_list, favorites=None):
    """
    Returns the default player index for dropdowns.
    Priority: 1. Favorites (if provided), 2. LeBron James, 3. First player alphabetically
    """
    if favorites and len(favorites) > 0:
        # If there are favorites and the first favorite is in the current season
        if favorites[0] in player_list:
            return player_list.index(favorites[0])
    
    # Try LeBron James as default
    if 'LeBron James' in player_list:
        return player_list.index('LeBron James')
    
    # Fall back to first player
    return 0

def generate_player_report_html(player_data, season, df_for_ranking=None, selected_metric='CPI'):
    """
    Generates an HTML report for a single player's clutch performance.
    """
    from datetime import datetime
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>NBA Clutch Analytics Report - {player_data['PLAYER_NAME']}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }}
            .header {{ background-color: #1D428A; color: white; padding: 20px; text-align: center; }}
            .content {{ background-color: white; padding: 30px; margin: 20px 0; border-radius: 8px; }}
            .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
            .stat-card {{ background-color: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; }}
            .stat-value {{ font-size: 24px; font-weight: bold; color: #1D428A; }}
            .stat-label {{ font-size: 14px; color: #666; }}
            .comparison {{ background-color: #e8f4fd; padding: 15px; margin: 20px 0; border-radius: 8px; }}
            .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 30px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>NBA Clutch Analytics Report</h1>
            <h2>{player_data['PLAYER_NAME']} ({player_data['TEAM_NAME']}) - {season} Season</h2>
        </div>
        
        <div class="content">
            <h3>Clutch Performance Overview</h3>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value">{player_data['CPI']:.3f}</div>
                    <div class="stat-label">Clutch Player Index</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{player_data['GP_clutch']:.0f}</div>
                    <div class="stat-label">Clutch Games Played</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{player_data['PPG_clutch']:.1f}</div>
                    <div class="stat-label">Clutch PPG</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{player_data['FG_PCT_clutch']:.1%}</div>
                    <div class="stat-label">Clutch FG%</div>
                </div>
            </div>
            
            <h3>Clutch vs. Non-Clutch Comparison</h3>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value">{player_data['PPG_diff']:+.1f}</div>
                    <div class="stat-label">PPG Differential</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{player_data['FG_PCT_diff']:+.1%}</div>
                    <div class="stat-label">FG% Differential</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{player_data['AST_TO_RATIO_clutch']:.2f}</div>
                    <div class="stat-label">Clutch AST/TO Ratio</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{player_data['PLUS_MINUS_PER_GAME_clutch']:+.1f}</div>
                    <div class="stat-label">Clutch +/- Per Game</div>
                </div>
            </div>
    """
    
    if df_for_ranking is not None:
        df_for_ranking['Rank'] = df_for_ranking[selected_metric].rank(ascending=False, method='min')
        player_rank_series = df_for_ranking[df_for_ranking['PLAYER_NAME'] == player_data['PLAYER_NAME']]['Rank']
        
        if not player_rank_series.empty:
            player_rank = int(player_rank_series.values[0])
            total_players = len(df_for_ranking)
            html_content += f"""
            <div class="comparison">
                <h3>League Ranking</h3>
                <p><strong>{player_data['PLAYER_NAME']}</strong> ranks <strong>#{player_rank}</strong> out of {total_players} players 
                in {METRIC_NAME_MAP.get(selected_metric, selected_metric)} (minimum 10 clutch games played).</p>
            </div>
            """
    
    html_content += f"""
        </div>
        
        <div class="footer">
            Report generated on {datetime.now().strftime("%B %d, %Y at %I:%M %p")}<br>
            NBA Clutch Analytics Dashboard
        </div>
    </body>
    </html>
    """
    
    return html_content

def generate_comparison_report_html(p1_data, p2_data, season):
    """
    Generates an HTML report comparing two players' clutch performance.
    """
    from datetime import datetime
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>NBA Clutch Analytics Comparison - {p1_data['PLAYER_NAME']} vs {p2_data['PLAYER_NAME']}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }}
            .header {{ background-color: #1D428A; color: white; padding: 20px; text-align: center; }}
            .content {{ background-color: white; padding: 30px; margin: 20px 0; border-radius: 8px; }}
            .comparison-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 30px; margin: 20px 0; }}
            .player-section {{ border: 2px solid #1D428A; border-radius: 8px; padding: 20px; }}
            .player-name {{ color: #1D428A; font-size: 20px; font-weight: bold; margin-bottom: 15px; }}
            .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; }}
            .stat-card {{ background-color: #f8f9fa; padding: 12px; border-radius: 6px; text-align: center; }}
            .stat-value {{ font-size: 18px; font-weight: bold; color: #1D428A; }}
            .stat-label {{ font-size: 12px; color: #666; }}
            .winner {{ background-color: #d4edda; border-color: #c3e6cb; }}
            .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 30px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>NBA Clutch Analytics Comparison Report</h1>
            <h2>{p1_data['PLAYER_NAME']} vs {p2_data['PLAYER_NAME']} - {season} Season</h2>
        </div>
        
        <div class="content">
            <div class="comparison-grid">
                <div class="player-section">
                    <div class="player-name">{p1_data['PLAYER_NAME']} ({p1_data['TEAM_NAME']})</div>
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="stat-value">{p1_data['CPI']:.3f}</div>
                            <div class="stat-label">CPI</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">{p1_data['GP_clutch']:.0f}</div>
                            <div class="stat-label">Clutch GP</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">{p1_data['PPG_clutch']:.1f}</div>
                            <div class="stat-label">Clutch PPG</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">{p1_data['FG_PCT_clutch']:.1%}</div>
                            <div class="stat-label">Clutch FG%</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">{p1_data['FG_PCT_diff']:+.1%}</div>
                            <div class="stat-label">FG% Diff</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">{p1_data['AST_TO_RATIO_clutch']:.2f}</div>
                            <div class="stat-label">AST/TO</div>
                        </div>
                    </div>
                </div>
                
                <div class="player-section">
                    <div class="player-name">{p2_data['PLAYER_NAME']} ({p2_data['TEAM_NAME']})</div>
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="stat-value">{p2_data['CPI']:.3f}</div>
                            <div class="stat-label">CPI</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">{p2_data['GP_clutch']:.0f}</div>
                            <div class="stat-label">Clutch GP</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">{p2_data['PPG_clutch']:.1f}</div>
                            <div class="stat-label">Clutch PPG</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">{p2_data['FG_PCT_clutch']:.1%}</div>
                            <div class="stat-label">Clutch FG%</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">{p2_data['FG_PCT_diff']:+.1%}</div>
                            <div class="stat-label">FG% Diff</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">{p2_data['AST_TO_RATIO_clutch']:.2f}</div>
                            <div class="stat-label">AST/TO</div>
                        </div>
                    </div>
                </div>
            </div>
            
            <h3>Key Comparisons</h3>
            <ul>
                <li><strong>Higher CPI:</strong> {p1_data['PLAYER_NAME'] if p1_data['CPI'] > p2_data['CPI'] else p2_data['PLAYER_NAME']} ({max(p1_data['CPI'], p2_data['CPI']):.3f} vs {min(p1_data['CPI'], p2_data['CPI']):.3f})</li>
                <li><strong>Better Clutch FG%:</strong> {p1_data['PLAYER_NAME'] if p1_data['FG_PCT_clutch'] > p2_data['FG_PCT_clutch'] else p2_data['PLAYER_NAME']} ({max(p1_data['FG_PCT_clutch'], p2_data['FG_PCT_clutch']):.1%} vs {min(p1_data['FG_PCT_clutch'], p2_data['FG_PCT_clutch']):.1%})</li>
                <li><strong>Higher Clutch PPG:</strong> {p1_data['PLAYER_NAME'] if p1_data['PPG_clutch'] > p2_data['PPG_clutch'] else p2_data['PLAYER_NAME']} ({max(p1_data['PPG_clutch'], p2_data['PPG_clutch']):.1f} vs {min(p1_data['PPG_clutch'], p2_data['PPG_clutch']):.1f})</li>
            </ul>
        </div>
        
        <div class="footer">
            Report generated on {datetime.now().strftime("%B %d, %Y at %I:%M %p")}<br>
            NBA Clutch Analytics Dashboard
        </div>
    </body>
    </html>
    """
    
    return html_content