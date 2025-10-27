# Save this file as modules/data_loader.py

import pandas as pd
import numpy as np
import os
from sklearn.preprocessing import StandardScaler

# --- Configuration ---
RAW_DATA_DIR = 'data/raw'
PROCESSED_DATA_DIR = 'data/processed'

# Define file paths
RAW_FILES = {
    'games': os.path.join(RAW_DATA_DIR, 'games.csv'),
    'details': os.path.join(RAW_DATA_DIR, 'games_details.csv'),
    'teams': os.path.join(RAW_DATA_DIR, 'teams.csv'),
    'ranking': os.path.join(RAW_DATA_DIR, 'ranking.csv')
}

PROCESSED_FILES = {
    'player': os.path.join(PROCESSED_DATA_DIR, 'player_performance.csv'),
    'team': os.path.join(PROCESSED_DATA_DIR, 'team_performance.csv')
}

# --- Helper Functions ---

def convert_min_to_decimal(min_str):
    """Converts 'MM:SS' or 'HH:MM:SS' string to decimal minutes."""
    if pd.isna(min_str) or min_str in ['DNP', 'N/A', '']:
        return 0.0
    
    parts = str(min_str).split(':')
    try:
        if len(parts) == 2:
            minutes = float(parts[0])
            seconds = float(parts[1])
            return minutes + (seconds / 60.0)
        elif len(parts) == 3: # Handle 'HH:MM:SS' if present
            hours = float(parts[0])
            minutes = float(parts[1])
            seconds = float(parts[2])
            return (hours * 60) + minutes + (seconds / 60.0)
        else: # Handle just minutes
            return float(parts[0])
    except ValueError:
        return 0.0

def calculate_cpi(df, min_clutch_gp=5):
    """
    Calculates the Clutch Player Index (CPI) using z-score normalization.
    Uses a tiered approach: full CPI for players with ≥5 games, adjusted CPI for players with <5 games.
    CPI is never 0 - minimum threshold players get a baseline score.
    """
    
    # Initialize CPI column
    df['CPI'] = np.nan
    
    # 1. Separate players into tiers based on clutch games played
    high_volume = df[df['GP_clutch'] >= min_clutch_gp].copy()
    low_volume = df[(df['GP_clutch'] > 0) & (df['GP_clutch'] < min_clutch_gp)].copy()
    
    if high_volume.empty and low_volume.empty:
        df['CPI'] = 0.0
        return df

    # 2. Define metrics for CPI
    metrics_to_scale = [
        'PPG_clutch', 
        'FG_PCT_clutch', 
        'APG_clutch', 
        'TOPG_clutch', 
        'PLUS_MINUS_PER_GAME_clutch'
    ]
    
    # 3. Calculate CPI for high-volume players (≥5 clutch games)
    if not high_volume.empty:
        # Handle potential infinite values from division by zero
        high_volume.replace([np.inf, -np.inf], np.nan, inplace=True)
        
        # Impute NaNs with the mean of the column for scaling
        for col in metrics_to_scale:
            if col not in high_volume.columns:
                print(f"Warning: Metric {col} not found for CPI calculation.")
                continue
            high_volume[col] = high_volume[col].fillna(high_volume[col].mean())

        # Scale the metrics (Z-Score)
        scaler = StandardScaler()
        scaled_metrics = scaler.fit_transform(high_volume[metrics_to_scale])
        scaled_df = pd.DataFrame(scaled_metrics, columns=metrics_to_scale, index=high_volume.index)

        # Define weights
        weights = {
            'PPG_clutch': 0.30,
            'FG_PCT_clutch': 0.25,
            'APG_clutch': 0.15,
            'TOPG_clutch': -0.15,  # Penalize turnovers
            'PLUS_MINUS_PER_GAME_clutch': 0.15
        }

        # Calculate CPI for high-volume players
        cpi_high = (
            scaled_df['PPG_clutch'] * weights['PPG_clutch'] +
            scaled_df['FG_PCT_clutch'] * weights['FG_PCT_clutch'] +
            scaled_df['APG_clutch'] * weights['APG_clutch'] +
            scaled_df['TOPG_clutch'] * weights['TOPG_clutch'] +
            scaled_df['PLUS_MINUS_PER_GAME_clutch'] * weights['PLUS_MINUS_PER_GAME_clutch']
        )
        
        df.loc[high_volume.index, 'CPI'] = cpi_high
    
    # 4. Calculate adjusted CPI for low-volume players (<5 clutch games)
    if not low_volume.empty:
        # Use a simplified calculation based on raw performance metrics
        # Normalize each metric to 0-1 scale within low-volume group
        low_volume_clean = low_volume.copy()
        low_volume_clean.replace([np.inf, -np.inf], np.nan, inplace=True)
        
        # Fill NaNs with group means
        for col in metrics_to_scale:
            if col in low_volume_clean.columns:
                low_volume_clean[col] = low_volume_clean[col].fillna(low_volume_clean[col].mean())
        
        # Min-max normalization for low-volume players
        normalized_metrics = {}
        for col in metrics_to_scale:
            if col in low_volume_clean.columns:
                col_min = low_volume_clean[col].min()
                col_max = low_volume_clean[col].max()
                if col_max != col_min:
                    normalized_metrics[col] = (low_volume_clean[col] - col_min) / (col_max - col_min)
                else:
                    normalized_metrics[col] = 0.5  # Neutral score if all values are the same
        
        # Apply same weights but scale down by games played factor
        games_factor = low_volume_clean['GP_clutch'] / min_clutch_gp  # Scale factor based on games played
        
        cpi_low = pd.Series(0.0, index=low_volume_clean.index)
        weights = {
            'PPG_clutch': 0.30,
            'FG_PCT_clutch': 0.25,
            'APG_clutch': 0.15,
            'TOPG_clutch': -0.15,
            'PLUS_MINUS_PER_GAME_clutch': 0.15
        }
        
        for col, weight in weights.items():
            if col in normalized_metrics:
                if col == 'TOPG_clutch':
                    # For turnovers, invert the normalized score (lower is better)
                    cpi_low += (1 - normalized_metrics[col]) * weight
                else:
                    cpi_low += normalized_metrics[col] * weight
        
        # Apply games factor and ensure minimum baseline
        cpi_low = cpi_low * games_factor
        baseline_score = -2.0  # Minimum CPI score for low-volume players
        cpi_low = cpi_low.clip(lower=baseline_score)
        
        df.loc[low_volume_clean.index, 'CPI'] = cpi_low

    return df

# --- Main Processing Functions ---

def process_player_data(games, details, teams):
    """
    Processes and aggregates all player-level performance data.
    """
    print("Processing player data...")
    
    # 1. Clean games_details
    print("  Cleaning game details...")
    stat_cols = ['FGM', 'FGA', 'FG3M', 'FG3A', 'FTM', 'FTA', 'OREB', 'DREB', 
                   'REB', 'AST', 'STL', 'BLK', 'TO', 'PF', 'PTS', 'PLUS_MINUS']
    
    details[stat_cols] = details[stat_cols].fillna(0)
    details[stat_cols] = details[stat_cols].astype(float)
    details['MIN'] = details['MIN'].apply(convert_min_to_decimal)
    
    # Filter out players with 0 minutes, as they didn't play
    details = details[details['MIN'] > 0].copy()

    # 2. Merge data
    print("  Merging datasets...")
    # Add GAME info (SEASON, IS_CLUTCH_GAME) to details
    details_merged = details.merge(
        games[['GAME_ID', 'SEASON', 'IS_CLUTCH_GAME']], 
        on='GAME_ID',
        how='inner'
    )
    
    # Add TEAM info (TEAM_NAME) to details
    details_merged = details_merged.merge(
        teams[['TEAM_ID', 'TEAM_NAME']], 
        on='TEAM_ID'
    )

    # 3. Aggregate stats
    print("  Aggregating player stats...")
    group_by_cols = ['PLAYER_ID', 'PLAYER_NAME', 'TEAM_NAME', 'SEASON', 'IS_CLUTCH_GAME']
    
    agg_dict = {col: 'sum' for col in stat_cols + ['MIN']}
    agg_dict['GAME_ID'] = 'count' # This will be our Games Played (GP)
    
    player_agg = details_merged.groupby(group_by_cols).agg(agg_dict).reset_index()
    player_agg = player_agg.rename(columns={'GAME_ID': 'GP', 'TO': 'TOV'}) # Rename 'TO' to avoid keyword clash

    # Update stat_cols to reflect the renamed column
    pivot_stat_cols = [col if col != 'TO' else 'TOV' for col in stat_cols]

    # 4. Pivot table
    print("  Pivoting data to clutch vs. non-clutch...")
    player_pivot = player_agg.pivot_table(
        index=['PLAYER_ID', 'PLAYER_NAME', 'TEAM_NAME', 'SEASON'],
        columns='IS_CLUTCH_GAME',
        values=pivot_stat_cols + ['MIN', 'GP']
    ).reset_index()

    # Clean up multi-index columns
    player_pivot.columns = [
        f"{col[0]}_{'clutch' if col[1] else 'non_clutch'}" if isinstance(col[1], bool) else col[0] 
        for col in player_pivot.columns
    ]
    
    # Fill NaNs for players who *only* played in one type of game
    stat_cols_all = [f"{col}_{suffix}" for col in pivot_stat_cols + ['MIN', 'GP'] for suffix in ['clutch', 'non_clutch']]
    player_pivot[stat_cols_all] = player_pivot[stat_cols_all].fillna(0)

    # 5. Calculate final metrics
    print("  Calculating final per-game and efficiency metrics...")
    
    # Calculate per-game stats
    for suffix in ['clutch', 'non_clutch']:
        gp_col = f'GP_{suffix}'
        min_col = f'MIN_{suffix}'
        
        # Avoid division by zero
        player_pivot[gp_col] = player_pivot[gp_col].replace(0, 1) # Use 1 to avoid DivByZero, stats will be 0 anyway
        player_pivot[min_col] = player_pivot[min_col].replace(0, 1)

        player_pivot[f'PPG_{suffix}'] = player_pivot[f'PTS_{suffix}'] / player_pivot[gp_col]
        player_pivot[f'APG_{suffix}'] = player_pivot[f'AST_{suffix}'] / player_pivot[gp_col]
        player_pivot[f'RPG_{suffix}'] = player_pivot[f'REB_{suffix}'] / player_pivot[gp_col]
        player_pivot[f'TOPG_{suffix}'] = player_pivot[f'TOV_{suffix}'] / player_pivot[gp_col]
        player_pivot[f'PLUS_MINUS_PER_GAME_{suffix}'] = player_pivot[f'PLUS_MINUS_{suffix}'] / player_pivot[gp_col]
        
        player_pivot[f'FG_PCT_{suffix}'] = player_pivot[f'FGM_{suffix}'] / player_pivot[f'FGA_{suffix}'].replace(0, 1)
        player_pivot[f'FG3_PCT_{suffix}'] = player_pivot[f'FG3M_{suffix}'] / player_pivot[f'FG3A_{suffix}'].replace(0, 1)
        player_pivot[f'FT_PCT_{suffix}'] = player_pivot[f'FTM_{suffix}'] / player_pivot[f'FTA_{suffix}'].replace(0, 1)
        
        player_pivot[f'AST_TO_RATIO_{suffix}'] = player_pivot[f'AST_{suffix}'] / player_pivot[f'TOV_{suffix}'].replace(0, 1)
        
        # Re-set GP for players with 0 games to 0 (we set to 1 to avoid errors)
        player_pivot[gp_col] = np.where(player_pivot[f'MIN_{suffix}'] == 1, 0, player_pivot[gp_col])


    # Calculate differential metrics
    player_pivot['FG_PCT_diff'] = player_pivot['FG_PCT_clutch'] - player_pivot['FG_PCT_non_clutch']
    player_pivot['PPG_diff'] = player_pivot['PPG_clutch'] - player_pivot['PPG_non_clutch']
    player_pivot['AST_TO_RATIO_diff'] = player_pivot['AST_TO_RATIO_clutch'] - player_pivot['AST_TO_RATIO_non_clutch']

    # 6. Calculate CPI
    print("  Calculating Clutch Player Index (CPI)...")
    player_performance = calculate_cpi(player_pivot)
    
    return player_performance

def process_team_data(games, teams):
    """
    Processes and aggregates all team-level performance data.
    """
    print("Processing team data...")
    
    # Melt games data to get one row per team-game
    games_home = games[['GAME_ID', 'SEASON', 'IS_CLUTCH_GAME', 'HOME_TEAM_ID', 'HOME_TEAM_WINS']]
    games_visitor = games[['GAME_ID', 'SEASON', 'IS_CLUTCH_GAME', 'VISITOR_TEAM_ID', 'HOME_TEAM_WINS']]
    
    games_home = games_home.rename(columns={'HOME_TEAM_ID': 'TEAM_ID', 'HOME_TEAM_WINS': 'WIN'})
    games_visitor = games_visitor.rename(columns={'VISITOR_TEAM_ID': 'TEAM_ID', 'HOME_TEAM_WINS': 'WIN'})
    games_visitor['WIN'] = 1 - games_visitor['WIN'] # Invert win for visitor
    
    team_games = pd.concat([games_home, games_visitor])
    
    # Aggregate stats
    team_agg = team_games.groupby(['TEAM_ID', 'SEASON', 'IS_CLUTCH_GAME']).agg(
        GP=('GAME_ID', 'count'),
        WINS=('WIN', 'sum')
    ).reset_index()
    
    team_agg['WIN_PCT'] = team_agg['WINS'] / team_agg['GP']
    
    # Pivot
    team_pivot = team_agg.pivot_table(
        index=['TEAM_ID', 'SEASON'],
        columns='IS_CLUTCH_GAME',
        values=['GP', 'WINS', 'WIN_PCT']
    ).reset_index()
    
    # Clean columns
    team_pivot.columns = [
        f"{col[0]}_{'clutch' if col[1] else 'non_clutch'}" if isinstance(col[1], bool) else col[0] 
        for col in team_pivot.columns
    ]
    
    # Add team names
    team_performance = team_pivot.merge(teams[['TEAM_ID', 'TEAM_NAME']], on='TEAM_ID')
    
    # Fill NaNs
    team_performance = team_performance.fillna(0)
    
    return team_performance

def run_processing():
    """
    Main function to run the entire data processing pipeline.
    """
    print("Starting data processing pipeline...")
    
    # Create processed directory if it doesn't exist
    if not os.path.exists(PROCESSED_DATA_DIR):
        os.makedirs(PROCESSED_DATA_DIR)
        
    # --- Load Raw Data ---
    try:
        print("Loading raw files...")
        games_raw = pd.read_csv(RAW_FILES['games'])
        details_raw = pd.read_csv(RAW_FILES['details'], low_memory=False)
        teams_raw = pd.read_csv(RAW_FILES['teams'])
    except FileNotFoundError as e:
        print(f"Error: Raw file not found. {e}")
        print("Please ensure 'games.csv', 'games_details.csv', and 'teams.csv' are in the 'data/raw' directory.")
        return

    # --- Pre-process Games and Teams ---
    print("Pre-processing games and teams...")
    # Define "Clutch Game"
    games_raw['SCORE_DIFF'] = (games_raw['PTS_home'] - games_raw['PTS_away']).abs()
    games_raw['IS_CLUTCH_GAME'] = (games_raw['SCORE_DIFF'] <= 5) & (games_raw['SCORE_DIFF'] >= 0)
    games_raw['GAME_DATE_EST'] = pd.to_datetime(games_raw['GAME_DATE_EST'])
    
    # Clean Teams
    teams_raw['TEAM_NAME'] = teams_raw['CITY'] + ' ' + teams_raw['NICKNAME']
    teams_clean = teams_raw[['TEAM_ID', 'TEAM_NAME']]

    # --- Run Processors ---
    player_performance = process_player_data(games_raw, details_raw, teams_clean)
    team_performance = process_team_data(games_raw, teams_clean)

    # --- Save Processed Data ---
    try:
        print(f"Saving processed data to {PROCESSED_DATA_DIR}...")
        player_performance.to_csv(PROCESSED_FILES['player'], index=False)
        team_performance.to_csv(PROCESSED_FILES['team'], index=False)
        print("---")
        print("Data processing complete!")
        print(f"Player data saved to: {PROCESSED_FILES['player']}")
        print(f"Team data saved to: {PROCESSED_FILES['team']}")
        print("---")
    except IOError as e:
        print(f"Error saving processed files: {e}")

if __name__ == "__main__":
    # To run this script, execute: python modules/data_loader.py
    run_processing()