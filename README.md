# 📊 Global Tech Layoff Analytics

A MySQL-based relational database system analyzing 4300+ 
real-world global tech layoffs from 2020 to 2024, with an 
ML-powered trend predictor.

## 🔥 Features
- 5 normalized MySQL tables (3NF)
- 4319 real layoff records
- 15+ SQL queries (basic to advanced)
- Interactive Streamlit dashboard
- 🔮 ML Layoff Trend Predictor (Random Forest, Gradient Boosting)
- Industry comparison tool
- Geographic world map
- Live SQL Explorer

## 📁 Project Structure
- `app_updated.py` — Main Streamlit dashboard
- `ml_predictor.py` — ML prediction engine
- `import_data.py` — CSV data importer
- `queries.sql` — All SQL queries
- `layoffs.csv` — Raw dataset
- `requirements.txt` — Python dependencies

## 🛠️ Tech Stack
- MySQL 8.0
- Python 3.x
- Streamlit
- Pandas
- Plotly
- Scikit-learn
- mysql-connector-python

## 📊 Dataset
- Source: layoffs.fyi & Kaggle
- Records: 4,319 layoff events
- Period: 2020–2024
- Companies: 1,600+
- Countries: 50+

## 🚀 How to Run
1. Clone the repository
2. Install dependencies:
   pip install -r requirements.txt
3. Set up MySQL database using import_data.py
4. Run the dashboard:
   python -m streamlit run app_updated.py

## 🔮 ML Predictor
- Models: Random Forest, Gradient Boosting, Linear Regression
- Predicts future layoffs by industry and country
- Shows confidence bands and risk assessment
- Feature importance visualization
