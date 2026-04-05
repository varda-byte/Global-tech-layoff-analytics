# 📊 Global Tech Layoff Analytics

A MySQL-based relational database system analyzing 4300+ 
real-world global tech layoffs from 2020 to 2024.

## 🔥 Features
- 5 normalized MySQL tables (3NF)
- 4319 real layoff records
- 15+ SQL queries (basic to advanced)
- Interactive Streamlit dashboard
- Industry comparison tool
- Economic period analysis
- Live SQL Explorer

## 📁 Project Structure
- `app.py` — Streamlit dashboard
- `import_data.py` — CSV data importer
- `queries.sql` — All SQL queries
- `layoffs.csv` — Raw dataset

## 🛠️ Technologies Used
- MySQL 8.0
- Python 3.x
- Streamlit
- Pandas
- Plotly
- mysql-connector-python

## 📊 Dataset
Source: layoffs.fyi & Kaggle
Records: 4319 layoff events
Period: 2020–2024
Companies: 1600+
Countries: 50+

## 🚀 How to Run
1. Import database using import_data.py
2. Run: python -m streamlit run app.py
3. Open browser at localhost:8501
