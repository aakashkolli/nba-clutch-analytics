import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score, mean_absolute_error
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.feature_selection import SelectKBest, f_regression
import streamlit as st

@st.cache_data
def get_model_data(player_df):
    """
    Engineers enhanced features to predict next season's CPI based on the current season.
    """
    # Sort by player and season to ensure correct shifting
    df = player_df.sort_values(by=['PLAYER_ID', 'SEASON'])
    
    # Enhanced feature engineering
    base_features = [
        'GP_clutch', 'PPG_clutch', 'FG_PCT_clutch', 'FG3_PCT_clutch', 
        'AST_TO_RATIO_clutch', 'PLUS_MINUS_PER_GAME_clutch', 
        'PPG_diff', 'FG_PCT_diff', 'GP_non_clutch', 'PPG_non_clutch',
        'RPG_clutch', 'APG_clutch', 'TOPG_clutch'
    ]
    
    # Create rolling averages for stability (2-year rolling means)
    df['CPI_2yr_avg'] = df.groupby('PLAYER_ID')['CPI'].rolling(2, min_periods=1).mean().reset_index(0, drop=True)
    df['PPG_clutch_2yr_avg'] = df.groupby('PLAYER_ID')['PPG_clutch'].rolling(2, min_periods=1).mean().reset_index(0, drop=True)
    df['FG_PCT_clutch_2yr_avg'] = df.groupby('PLAYER_ID')['FG_PCT_clutch'].rolling(2, min_periods=1).mean().reset_index(0, drop=True)
    
    # Create interaction features
    df['PPG_times_FG_PCT'] = df['PPG_clutch'] * df['FG_PCT_clutch']
    df['Games_consistency'] = df['GP_clutch'] / (df['GP_clutch'] + df['GP_non_clutch'])
    df['Clutch_volume'] = df['GP_clutch'] * df['PPG_clutch']
    
    # Age proxy (years since first season)
    df['experience'] = df.groupby('PLAYER_ID')['SEASON'].rank() - 1
    
    # Performance stability (coefficient of variation)
    df['PPG_stability'] = df.groupby('PLAYER_ID')['PPG_clutch'].rolling(3, min_periods=2).std().reset_index(0, drop=True)
    df['PPG_stability'] = df['PPG_stability'].fillna(df['PPG_stability'].median())
    
    enhanced_features = base_features + [
        'CPI_2yr_avg', 'PPG_clutch_2yr_avg', 'FG_PCT_clutch_2yr_avg',
        'PPG_times_FG_PCT', 'Games_consistency', 'Clutch_volume',
        'experience', 'PPG_stability'
    ]
    
    target = 'CPI'
    
    # Use groupby().shift(-1) to get next season's CPI as the target
    df['TARGET_CPI'] = df.groupby('PLAYER_ID')[target].shift(-1)
    
    # Filter for players with sufficient data (at least 5 clutch games)
    df_filtered = df[df['GP_clutch'] >= 5].copy()
    
    # Drop rows with no target or missing features
    df_model = df_filtered.dropna(subset=['TARGET_CPI'] + enhanced_features)
    
    # Remove outliers using IQR method
    Q1 = df_model['TARGET_CPI'].quantile(0.25)
    Q3 = df_model['TARGET_CPI'].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    df_model = df_model[(df_model['TARGET_CPI'] >= lower_bound) & (df_model['TARGET_CPI'] <= upper_bound)]
    
    # Define X and y
    X = df_model[enhanced_features]
    y = df_model['TARGET_CPI']
    
    return X, y, enhanced_features, df_model

@st.cache_resource
def train_model(X, y):
    """
    Trains an optimized ensemble model with hyperparameter tuning and regularization.
    """
    if X.empty or y.empty or len(X) < 100:
        return None, None, None, None, None, None
        
    # Stratified split to ensure balanced training/test sets
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=pd.cut(y, bins=5, labels=False)
    )
    
    # Use RobustScaler to handle outliers better
    scaler = RobustScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Feature selection to reduce overfitting
    selector = SelectKBest(score_func=f_regression, k=min(12, X.shape[1]))
    X_train_selected = selector.fit_transform(X_train_scaled, y_train)
    X_test_selected = selector.transform(X_test_scaled)
    
    # Ensemble of models with hyperparameter tuning
    models = {
        'rf': RandomForestRegressor(
            n_estimators=200,
            max_depth=8,
            min_samples_split=10,
            min_samples_leaf=5,
            max_features='sqrt',
            random_state=42,
            n_jobs=-1
        ),
        'gbm': GradientBoostingRegressor(
            n_estimators=150,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            random_state=42
        ),
        'ridge': Ridge(alpha=10.0)
    }
    
    # Train all models and combine predictions
    trained_models = {}
    predictions_train = np.zeros(len(y_train))
    predictions_test = np.zeros(len(y_test))
    
    for name, model in models.items():
        model.fit(X_train_selected, y_train)
        trained_models[name] = model
        
        # Get predictions
        pred_train = model.predict(X_train_selected)
        pred_test = model.predict(X_test_selected)
        
        # Ensemble weights (RF: 0.5, GBM: 0.3, Ridge: 0.2)
        weights = {'rf': 0.5, 'gbm': 0.3, 'ridge': 0.2}
        predictions_train += pred_train * weights[name]
        predictions_test += pred_test * weights[name]
    
    # Calculate metrics
    train_r2 = r2_score(y_train, predictions_train)
    test_r2 = r2_score(y_test, predictions_test)
    mae = mean_absolute_error(y_test, predictions_test)
    
    # Calculate RMSE
    rmse = np.sqrt(np.mean((y_test - predictions_test) ** 2))
    
    # Store ensemble components for prediction
    ensemble_model = {
        'models': trained_models,
        'selector': selector,
        'weights': {'rf': 0.5, 'gbm': 0.3, 'ridge': 0.2}
    }
    
    return ensemble_model, scaler, test_r2, mae, train_r2, rmse

def get_predictions(player_df, selected_season, ensemble_model, scaler, features):
    """
    Generates predictions for all players from the selected season using the ensemble model.
    """
    # Get all player data from the selected season
    current_season_data = player_df[player_df['SEASON'] == selected_season].copy()
    
    # Re-engineer features for the current season data (same as in get_model_data)
    df = player_df.sort_values(by=['PLAYER_ID', 'SEASON'])
    
    # Create rolling averages for stability (2-year rolling means)
    df['CPI_2yr_avg'] = df.groupby('PLAYER_ID')['CPI'].rolling(2, min_periods=1).mean().reset_index(0, drop=True)
    df['PPG_clutch_2yr_avg'] = df.groupby('PLAYER_ID')['PPG_clutch'].rolling(2, min_periods=1).mean().reset_index(0, drop=True)
    df['FG_PCT_clutch_2yr_avg'] = df.groupby('PLAYER_ID')['FG_PCT_clutch'].rolling(2, min_periods=1).mean().reset_index(0, drop=True)
    
    # Create interaction features
    df['PPG_times_FG_PCT'] = df['PPG_clutch'] * df['FG_PCT_clutch']
    df['Games_consistency'] = df['GP_clutch'] / (df['GP_clutch'] + df['GP_non_clutch'])
    df['Clutch_volume'] = df['GP_clutch'] * df['PPG_clutch']
    
    # Age proxy (years since first season)
    df['experience'] = df.groupby('PLAYER_ID')['SEASON'].rank() - 1
    
    # Performance stability (coefficient of variation)
    df['PPG_stability'] = df.groupby('PLAYER_ID')['PPG_clutch'].rolling(3, min_periods=2).std().reset_index(0, drop=True)
    df['PPG_stability'] = df['PPG_stability'].fillna(df['PPG_stability'].median())
    
    # Get the enhanced data for the selected season
    current_season_enhanced = df[df['SEASON'] == selected_season].copy()
    
    # Ensure data has all required features
    current_season_enhanced = current_season_enhanced.dropna(subset=features)
    
    if current_season_enhanced.empty:
        return pd.DataFrame()
        
    # Prepare data for prediction
    X_pred = current_season_enhanced[features]
    X_pred_scaled = scaler.transform(X_pred)
    X_pred_selected = ensemble_model['selector'].transform(X_pred_scaled)
    
    # Make ensemble predictions
    ensemble_predictions = np.zeros(len(X_pred))
    for name, model in ensemble_model['models'].items():
        pred = model.predict(X_pred_selected)
        ensemble_predictions += pred * ensemble_model['weights'][name]
    
    # Create a results dataframe
    results_df = current_season_enhanced[['PLAYER_NAME', 'TEAM_NAME']].copy()
    results_df[f'Predicted CPI ({selected_season + 1})'] = ensemble_predictions
    results_df = results_df.sort_values(by=f'Predicted CPI ({selected_season + 1})', ascending=False)
    
    return results_df