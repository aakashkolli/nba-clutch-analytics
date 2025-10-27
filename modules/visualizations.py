# Save this file as modules/visualizations.py

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from modules.utils import METRIC_NAME_MAP

# --- Plotting Theme ---
PLOT_TEMPLATE = "plotly_white"
NBA_BLUE = "#1D428A"
NBA_RED = "#C8102E"
NBA_GRAY = "#6C6D6F"

def _format_fig(fig, title):
    """Helper to apply standard layout updates."""
    fig.update_layout(
        title={'text': f"<b>{title}</b>", 'x': 0.5, 'font': {'size': 20, 'color': '#06192D'}},
        template=PLOT_TEMPLATE,
        font=dict(family="Roboto, Arial, sans-serif", color=NBA_GRAY),
        xaxis=dict(title_font=dict(size=14), tickfont=dict(size=12)),
        yaxis=dict(title_font=dict(size=14), tickfont=dict(size=12)),
        legend=dict(font=dict(size=12)),
        margin=dict(l=40, r=40, t=60, b=40)
    )
    return fig

def plot_player_kpis(player_data, compare_data=None):
    """
    Creates a set of bullet charts (styled as metrics) for a player's
    clutch vs. non-clutch performance.
    Optionally includes a second player for comparison.
    """
    metrics = [
        ('PPG', 'PPG_clutch', 'PPG_non_clutch'),
        ('FG%', 'FG_PCT_clutch', 'FG_PCT_non_clutch'),
        ('3P%', 'FG3_PCT_clutch', 'FG3_PCT_non_clutch'),
        ('AST/TO', 'AST_TO_RATIO_clutch', 'AST_TO_RATIO_non_clutch'),
    ]

    fig = go.Figure()
    
    num_metrics = len(metrics)
    has_compare = compare_data is not None
    
    for i, (label, clutch_col, non_clutch_col) in enumerate(metrics):
        # --- Player 1 (Main) ---
        clutch_val = player_data.get(clutch_col, 0)
        non_clutch_val = player_data.get(non_clutch_col, 0)
        
        # --- Player 2 (Compare) ---
        clutch_val_p2 = compare_data.get(clutch_col, 0) if has_compare else 0
        non_clutch_val_p2 = compare_data.get(non_clutch_col, 0) if has_compare else 0
        
        # Determine a reasonable max for the gauge
        gauge_max = max(clutch_val, non_clutch_val, clutch_val_p2, non_clutch_val_p2) * 1.5
        if gauge_max == 0:
            gauge_max = 1.0 if '%' in label else 10.0 # Default max

        # Add Player 1's Trace
        fig.add_trace(go.Indicator(
            mode="number+gauge+delta",
            value=clutch_val,
            delta={'reference': non_clutch_val, 'relative': False, 
                   'valueformat': '.3f' if '%' in label else '.2f'},
            domain={'row': 0, 'column': i},
            title={'text': f"<b>{label}</b><br>(vs. Non-Clutch)"},
            number={'valueformat': '.3f' if '%' in label else '.2f'},
            gauge={
                'shape': "bullet",
                'axis': {'range': [0, gauge_max]},
                'threshold': { # Non-Clutch value
                    'line': {'color': NBA_GRAY, 'width': 2},
                    'thickness': 0.75,
                    'value': non_clutch_val
                },
                'bar': {'color': NBA_BLUE} # Clutch value
            }
        ))
        
        # Add Player 2's Trace (if applicable)
        if has_compare:
            fig.add_trace(go.Indicator(
                mode="gauge", # No number or delta for P2
                value=clutch_val_p2,
                domain={'row': 1, 'column': i},
                gauge={
                    'shape': "bullet",
                    'axis': {'range': [0, gauge_max]},
                    'threshold': { # Non-Clutch value
                        'line': {'color': NBA_GRAY, 'width': 2},
                        'thickness': 0.75,
                        'value': non_clutch_val_p2
                    },
                    'bar': {'color': NBA_RED} # Clutch value
                }
            ))

    # Define the grid layout
    rows = 2 if has_compare else 1
    fig.update_layout(
        grid={'rows': rows, 'columns': num_metrics, 'pattern': "independent"},
        template=PLOT_TEMPLATE,
        height=150 * rows,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    return fig

def plot_league_distribution(df, player_data, metric_col):
    """
    Plots a histogram of the league distribution for a given metric
    and highlights the selected player's position.
    """
    metric_label = METRIC_NAME_MAP.get(metric_col, metric_col)
    
    if player_data is None or metric_col not in df.columns:
        return go.Figure().update_layout(title="Metric not found.")

    # Filter out extreme outliers for a better plot
    q_low = df[metric_col].quantile(0.01)
    q_high = df[metric_col].quantile(0.99)
    df_filtered = df[(df[metric_col] > q_low) & (df[metric_col] < q_high)]
    
    player_value = player_data.get(metric_col, 0)
    player_name = player_data.get('PLAYER_NAME', 'Selected Player')
    
    fig = px.histogram(df_filtered, x=metric_col, nbins=50, 
                       opacity=0.7, color_discrete_sequence=[NBA_BLUE])
    
    fig.add_vline(
        x=player_value, 
        line_width=3, 
        line_dash="dash", 
        line_color=NBA_RED,
        annotation_text=f"{player_name}: {player_value:.2f}",
        annotation_position="top left",
        annotation_font=dict(color=NBA_RED, size=14)
    )
    
    fig = _format_fig(fig, f"League Distribution: {metric_label}")
    fig.update_layout(showlegend=False, yaxis_title="Player Count", xaxis_title=metric_label)
    return fig

def plot_team_win_pct(team_data):
    """
    Compares a team's win percentage in clutch vs. non-clutch games.
    """
    if team_data is None:
        return go.Figure().update_layout(title="No data for this team.")

    clutch_pct = team_data.get('WIN_PCT_clutch', 0)
    non_clutch_pct = team_data.get('WIN_PCT_non_clutch', 0)
    
    data = {
        'Game Type': ['Clutch Games', 'Non-Clutch Games'],
        'Win Percentage': [clutch_pct, non_clutch_pct],
        'Games Played': [team_data.get('GP_clutch', 0), team_data.get('GP_non_clutch', 0)]
    }
    df = pd.DataFrame(data)

    fig = px.bar(
        df, x='Game Type', y='Win Percentage', 
        color='Game Type', 
        color_discrete_map={'Clutch Games': NBA_RED, 'Non-Clutch Games': NBA_GRAY},
        text_auto='.1%',
        hover_data=['Games Played']
    )
    fig.update_layout(yaxis_range=[0,1], showlegend=False, yaxis_title="Win Percentage", xaxis_title=None)
    fig = _format_fig(fig, f"{team_data.get('TEAM_NAME')} - Win % (Clutch vs. Non-Clutch)")
    return fig

def plot_simulation_results(old_stats, new_stats):
    """
    Displays the results of the simulation as a grouped bar chart.
    """
    df = pd.DataFrame([old_stats, new_stats], index=['Current', 'Simulated']).T.reset_index()
    df.columns = ['Metric', 'Current', 'Simulated']
    df_melted = df.melt(id_vars='Metric', var_name='Scenario', value_name='Value')

    fig = px.bar(
        df_melted, 
        x='Metric', 
        y='Value', 
        color='Scenario', 
        barmode='group',
        color_discrete_map={'Current': NBA_GRAY, 'Simulated': NBA_BLUE},
        text_auto='.2f'
    )
    fig = _format_fig(fig, "Simulation Results: Current vs. Simulated")
    fig.update_layout(xaxis_title=None, yaxis_title="Value")
    return fig

def plot_model_feature_importance(ensemble_model, feature_names):
    """
    Plots feature importances for the ensemble predictive model.
    """
    if ensemble_model is None or 'models' not in ensemble_model:
        return go.Figure().update_layout(title="Model not available for feature importance.")
    
    # Get selected features from the feature selector
    selected_mask = ensemble_model['selector'].get_support()
    selected_features = [feature_names[i] for i in range(len(feature_names)) if selected_mask[i]]
    
    # Calculate weighted feature importance from ensemble
    total_importance = None
    
    for name, model in ensemble_model['models'].items():
        if hasattr(model, 'feature_importances_'):
            importances = model.feature_importances_
        elif hasattr(model, 'coef_'):
            importances = abs(model.coef_)  # Use absolute values for Ridge
        else:
            continue
            
        # Weight by ensemble weight
        weighted_importance = importances * ensemble_model['weights'][name]
        
        if total_importance is None:
            total_importance = weighted_importance
        else:
            total_importance += weighted_importance
    
    if total_importance is None:
        return go.Figure().update_layout(title="No feature importances available.")
        
    imp_df = pd.DataFrame({'Feature': selected_features, 'Importance': total_importance})
    imp_df = imp_df.sort_values(by='Importance', ascending=False).head(10)
    
    fig = px.bar(imp_df, x='Importance', y='Feature', orientation='h', 
                 color_discrete_sequence=[NBA_BLUE])
    fig = _format_fig(fig, "Top 10 Predictor Features for Next-Season CPI (Ensemble Model)")
    fig.update_layout(yaxis=dict(autorange="reversed"))
    return fig