print("Start imports...")
import sqlite3
import pandas as pd
print("Pandas imported")
import plotly.express as px
print("Plotly imported")
import os

DB_PATH = 'data/anomalies.db'

def test_plot():
    print(f"Checking DB at {DB_PATH}")
    if not os.path.exists(DB_PATH):
        print("DB not found")
        return

    print("Connecting to DB...")
    conn = sqlite3.connect(DB_PATH)
    query = "SELECT * FROM anomalies ORDER BY timestamp DESC LIMIT 1000"
    df = pd.read_sql_query(query, conn)
    conn.close()
    print(f"Loaded {len(df)} rows")

    print("Columns:", df.columns)
    print("Types:\n", df.dtypes)
    print("Head:\n", df[['velocity', 'prediction']].head())
    
    # Simulate app.py logic
    df['velocity'] = pd.to_numeric(df['velocity'], errors='coerce').fillna(0)
    df['prediction'] = df['prediction'].astype(str).str.strip()
    
    print("After processing types:\n", df.dtypes)
    print("Unique predictions:", df['prediction'].unique())
    print("Velocity stats:\n", df['velocity'].describe())

    try:
        fig = px.histogram(
            df,
            x="velocity",
            color="prediction",
            title="Transaction Velocity Distribution"
        )
        print("Figure created successfully")
        # print(fig.layout)
    except Exception as e:
        print("Error creating figure:", e)

if __name__ == "__main__":
    test_plot()