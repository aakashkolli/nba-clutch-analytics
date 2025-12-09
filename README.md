# 🏀 NBA Clutch Analytics Dashboard

Live Demo: https://nbaclutch.streamlit.app/

A comprehensive **Streamlit-powered analytics platform** that analyzes NBA player and team performance in "clutch" situations - the moments when games are decided and legends are made.

![Python](https://img.shields.io/badge/python-v3.8+-blue.svg)
![Streamlit](https://img.shields.io/badge/streamlit-v1.28+-red.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## What is "Clutch" Performance?

**Clutch games** are defined as games decided by **5 points or fewer** - the high-pressure moments where true champions emerge. This dashboard goes beyond traditional box scores to reveal:

- Which players **elevate** their game under pressure
- Which players **struggle** when it matters most
- How **team dynamics** change in close games
- **Predictive insights** for future clutch performance


## Key Features

### **Multi-Page Analytics Suite**

| Page | Description | Key Insights |
||-|--|
| ** Home** | Top 15 clutch players overview | Real-time CPI rankings and trends |
| ** Player Profile** | Individual deep-dive analysis | Clutch vs non-clutch performance comparison |
| ** Team Profile** | Team-level clutch performance | Win rates and top performers in close games |
| ** Player Comparison** | Head-to-head clutch analysis | Side-by-side metrics and differentials |
| ** Scenario Simulator** | What-if usage modeling | Impact analysis of increased player usage |
| ** Predictive Model** | ML-powered future predictions | Next season's top clutch performers |

### **Analytics**

- **Clutch Player Index (CPI)**: Proprietary composite metric combining multiple performance indicators
- **Interactive Visualizations**: Powered by Plotly for dynamic data exploration
- **Downloadable Reports**: HTML-formatted player analysis reports
- **Machine Learning**: Ensemble model predicting future clutch performance

## Quick Start

### Prerequisites

- **Python 3.8+**
- **pip** package manager

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd nba_project
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Process the data** (one-time setup):
   ```bash
   python modules/data_loader.py
   ```

4. **Launch the dashboard**:
   ```bash
   streamlit run 0_Home.py
   ```

5. **Open your browser** to `http://localhost:8501`

## 📊 Data Sources & Methodology

### **Dataset Overview**
- **Games**: ~65,000 NBA games with scores and metadata
- **Game Details**: ~1.3M player-game records with detailed statistics
- **Teams**: Franchise information and naming
- **Time Period**: Multiple NBA seasons with comprehensive coverage

### **Clutch Definition**
```python
# A game is considered "clutch" if:
games['IS_CLUTCH_GAME'] = (games['SCORE_DIFF'] <= 5) & (games['SCORE_DIFF'] >= 0)
```

### **CPI Calculation (Clutch Player Index)**

Our proprietary **Clutch Player Index** uses an advanced ensemble approach:

#### **For High-Volume Players (≥5 clutch games):**
- **Z-score normalization** across all qualified players
- **Weighted composite** of key performance metrics:
  - Points per game (30%)
  - Field goal percentage (25%)
  - Assists per game (15%)
  - Plus/minus per game (15%)
  - Turnovers per game (-15%, penalty)

#### **For Low-Volume Players (<5 clutch games):**
- **Min-max normalization** within low-volume cohort
- **Games-played scaling factor** to account for sample size
- **Baseline score minimum** to ensure meaningful rankings


## Machine Learning Model

### **Architecture: Advanced Ensemble**

Our predictive model uses a **3-model ensemble** optimized for clutch performance prediction:

| Model | Weight | Purpose |
|-|--||
| **Random Forest** | 50% | Non-linear patterns, feature interactions |
| **Gradient Boosting** | 30% | Sequential learning, bias reduction |
| **Ridge Regression** | 20% | Linear baseline, regularization |

### **Enhanced Feature Engineering (21 Features)**

- **Base Statistics**: PPG, FG%, 3P%, AST/TO ratio, +/-
- **Rolling Averages**: 2-year stability metrics
- **Interaction Features**: PPG×FG%, clutch volume, consistency
- **Experience Tracking**: Years since debut (age proxy)
- **Performance Stability**: Coefficient of variation

### **Model Performance**

- **Training R²**: 0.502
- **Testing R²**: 0.337
- **MAE**: 0.250
- **RMSE**: 0.316


## Technical Implementation

### **Core Technologies**

- **Streamlit**: Web application framework
- **Pandas**: Data manipulation and analysis
- **Plotly**: Interactive visualizations
- **Scikit-learn**: Machine learning models
- **CSS**: Custom dark theme styling

### **Key Features**

- **Caching**: `@st.cache_data` for optimal performance
- **Session State**: Persistent user preferences
- **Responsive Design**: Container-width optimization
- **Error Handling**: Graceful fallbacks for missing data

### **Performance Optimizations**

- **Data preprocessing**: One-time heavy computations
- **Efficient filtering**: Indexed DataFrame operations
- **Lazy loading**: On-demand chart generation
- **Memory management**: Strategic cache clearing



## Usage Examples

### **Finding Clutch Performers**
```python
# Top clutch players with minimum 10 games
top_clutch = player_df[player_df['GP_clutch'] >= 10].nlargest(10, 'CPI')
```

### **Comparing Players**
```python
# Head-to-head clutch performance
player1_clutch = player_df[player_df['PLAYER_NAME'] == 'LeBron James']
player2_clutch = player_df[player_df['PLAYER_NAME'] == 'Stephen Curry']
```

### **Team Analysis**
```python
# Team clutch win rates
team_clutch_rate = team_df['WIN_PCT_clutch'].sort_values(ascending=False)
```



## Key Insights You Can Discover

### **Player-Level Analysis**
- **Elite Clutch Performers**: Players who elevate their game under pressure
- **Clutch Struggles**: Stars who underperform in high-pressure moments
- **Performance Differentials**: How much players improve/decline in clutch time
- **Consistency Metrics**: Who can be relied upon in crucial moments

### **Team-Level Insights**
- **Clutch Team Rankings**: Which franchises excel in close games
- **Role Player Impact**: How bench players perform under pressure
- **Season Trends**: Clutch performance evolution throughout seasons
- **Championship Correlation**: Relationship between clutch performance and success

### **Predictive Intelligence**
- **Future Stars**: Emerging clutch performers for next season
- **Usage Optimization**: How increased responsibility affects performance
- **Draft Insights**: Clutch potential of developing players
- **Trade Analysis**: Impact of player movement on clutch performance


### **Development Setup**
```bash
# Fork the repository
git clone <your-fork-url>
cd nba_project

# Create a development branch
git checkout -b feature/your-feature-name

# Make changes and test
streamlit run 0_Home.py

# Submit a pull request
```


## License

This project is licensed under the **MIT License**.



## Acknowledgments

- **NBA.com** for providing comprehensive basketball statistics
- **Streamlit** team for the amazing web framework
- **Plotly** for powerful visualization capabilities
- **Basketball analytics community** for inspiration and methodologies

