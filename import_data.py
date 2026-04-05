import pandas as pd
import mysql.connector
from datetime import datetime

# Connect to MySQL
conn = mysql.connector.connect(
    host="127.0.0.1",
    user="root",
    password="root123",
    database="layoff_analytics"
)

# Read CSV file
df = pd.read_csv('layoffs.csv')

# Clean data
df = df.where(pd.notnull(df), None)

# Fix date format
def fix_date(date_val):
    if date_val is None:
        return None
    try:
        return datetime.strptime(str(date_val), '%m/%d/%Y').strftime('%Y-%m-%d')
    except:
        return None

df['date'] = df['date'].apply(fix_date)

cursor = conn.cursor()

# Insert each row
for _, row in df.iterrows():
    sql = """INSERT INTO layoffs_staging 
    (company, location, total_laid_off, date, 
    percentage_laid_off, industry, source, 
    stage, funds_raised, country, date_added) 
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
    
    cursor.execute(sql, tuple(row))

conn.commit()
print("Data imported successfully!")
print(f"Total rows imported: {len(df)}")

cursor.close()
conn.close()