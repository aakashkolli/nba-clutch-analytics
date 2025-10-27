import streamlit as st
import pandas as pd
from modules.utils import (
    set_page_config, 
    inject_custom_css, 
    load_data, 
    get_season_data
)
from modules.models import get_model_data, train_model, get_predictions
from modules.visualizations import plot_model_feature_importance

set_page_config()
inject_custom_css()

player_df, team_df = load_data()
if player_df is None:
    st.stop()

player_df_season, team_df_season, selected_season = get_season_data(player_df, team_df)

st.header("Clutch Performance Predictive Model")
st.markdown("""
This page features a machine learning model (Random Forest Regressor) that predicts a player’s next-season Clutch Player Index (CPI) using their current-season performance.
""")

X, y, features, _ = get_model_data(player_df)
model, scaler, r2, mae, train_r2, rmse = train_model(X, y)

if model is None:
    st.error("Not enough data to train the model. More seasons are required.")
    st.stop()

st.subheader("Model Performance")
st.markdown("The model was trained on historical data and evaluated on a hold-out test set.")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Training R²", f"{train_r2:.3f}", help="R² score on training data - how well the model fits the training set.")
col2.metric("Testing R²", f"{r2:.3f}", help="R² score on test data - how well the model generalizes to unseen data.")
col3.metric("Mean Absolute Error", f"{mae:.3f}", help="The average absolute difference between predicted and actual CPI values.")
col4.metric("Root Mean Squared Error", f"{rmse:.3f}", help="Square root of the mean squared error - penalizes larger prediction errors more heavily.")

fig_imp = plot_model_feature_importance(model, features)
st.plotly_chart(fig_imp, use_container_width=True)

st.markdown("---")

st.header(f"Predicted Top 20 Clutch Players for {selected_season + 1}")
st.markdown(f"Based on player performance from the **{selected_season}** season.")

predictions_df = get_predictions(player_df, selected_season, model, scaler, features)

if predictions_df.empty:
    st.warning(f"No players in the {selected_season} season had the complete data required for prediction.")
else:
    st.dataframe(
        predictions_df.head(20).style
            .format({f'Predicted CPI ({selected_season + 1})': '{:.3f}'})
            .background_gradient(cmap='Greens', subset=[f'Predicted CPI ({selected_season + 1})']),
        width='stretch',
        hide_index=True
    )