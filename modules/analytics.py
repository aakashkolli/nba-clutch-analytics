import pandas as pd
import numpy as np

def get_player_profile(df, player_name, season):
    """
    Retrieves a single player's data row as a dictionary (or Series).
    """
    try:
        player_data = df[
            (df['PLAYER_NAME'] == player_name) & 
            (df['SEASON'] == season)
        ]
        if player_data.empty:
            return None
        return player_data.iloc[0]
    except Exception:
        return None

def run_simulation(player_profile, shot_increase_pct):
    """
    Simulates the impact of increased shot volume in clutch situations.

    Args:
        player_profile (pd.Series): A row from the player_performance df.
        shot_increase_pct (float): Pct increase in FGA (e.g., 10 for 10%).

    Returns:
        tuple: (dict_old_stats, dict_new_stats)
    """
    
    old_stats = {
        'PPG': player_profile.get('PPG_clutch', 0),
        'FGA_per_game': player_profile.get('FGA_clutch', 0) / player_profile.get('GP_clutch', 1),
        'TOPG': player_profile.get('TOPG_clutch', 0),
        'AST/TO': player_profile.get('AST_TO_RATIO_clutch', 0)
    }

    increase_factor = 1 + (shot_increase_pct / 100.0)
    new_fga_per_game = old_stats['FGA_per_game'] * increase_factor
    delta_fga = new_fga_per_game - old_stats['FGA_per_game']
    
    # Assume points-per-shot remains constant
    fg_pct = player_profile.get('FG_PCT_clutch', 0)
    # This accounts for 2s, 3s, and FTs from shooting fouls
    pts_per_fga = player_profile.get('PTS_clutch', 0) / player_profile.get('FGA_clutch', 1)
    
    delta_pts = delta_fga * pts_per_fga
    new_ppg = old_stats['PPG'] + delta_pts

    # 4. Simulate impact on turnovers
    # More shots/usage -> more turnovers.
    # We'll use a simple "turnover per FGA" rate as a proxy
    tov_per_fga = player_profile.get('TOV_clutch', 0) / player_profile.get('FGA_clutch', 1)
    
    # Assume a slight increase in turnover *rate* due to pressure
    # Let's say a 10% increase in FGA leads to a 5% increase in TOV_rate (0.5 elasticity)
    elasticity = 0.5 
    tov_rate_increase = (shot_increase_pct / 100.0) * elasticity
    new_tov_rate = tov_per_fga * (1 + tov_rate_increase)
    
    new_topg = old_stats['TOPG'] + (delta_fga * new_tov_rate)
    
    # 5. Calculate new AST/TO
    apg = player_profile.get('APG_clutch', 0) # Assume assists per game is constant
    new_ast_to = apg / (new_topg if new_topg > 0 else 1)

    new_stats = {
        'PPG': new_ppg,
        'FGA_per_game': new_fga_per_game,
        'TOPG': new_topg,
        'AST/TO': new_ast_to
    }
    
    return old_stats, new_stats
