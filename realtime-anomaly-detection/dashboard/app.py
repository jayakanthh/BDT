import streamlit as st
import sqlite3
import pandas as pd
import time
import plotly.express as px
import os

# Page Configuration
st.set_page_config(
    page_title="Real-Time Anomaly Detection Dashboard",
    page_icon="🚨",
    layout="wide",
)

st.title("🚨 Real-Time Anomaly Detection Dashboard")
st.markdown("### Monitoring Credit Card Transactions for Fraud/Anomalies")

# Ensure data directory exists
if not os.path.exists('../data'):
    os.makedirs('../data')

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'anomalies.db')

def load_data():
    try:
        if not os.path.exists(DB_PATH):
            return pd.DataFrame(), 0, 0
        conn = sqlite3.connect(DB_PATH, timeout=10)
        
        # Get total counts
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM anomalies")
        total_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM anomalies WHERE prediction = 'Anomaly'")
        total_anomalies_count = cursor.fetchone()[0]
        
        # Order by timestamp since we don't have an auto-increment ID
        query = "SELECT * FROM anomalies ORDER BY timestamp DESC LIMIT 1000"
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df, total_count, total_anomalies_count
    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.write(f"DEBUG Path: {DB_PATH}")
        return pd.DataFrame(), 0, 0

# Create Tabs
tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📡 Live Data Stream", "🗄️ Database View"])

with tab1:
    # Placeholders for metrics
    col1, col2, col3 = st.columns(3)
    metric_total = col1.empty()
    metric_anomalies = col2.empty()
    metric_ratio = col3.empty()
    
    # Placeholder for charts
    chart_placeholder = st.empty()
    table_placeholder = st.empty()

with tab2:
    st.subheader("Live Transaction Stream")
    live_table_placeholder = st.empty()

with tab3:
    st.subheader("🗄️ Historical Database Records")
    
    # Reload button for this tab
    if st.button("Reload Database Data"):
        st.cache_data.clear()
        
    # Filters
    col_filter1, col_filter2 = st.columns(2)
    with col_filter1:
        # Default to showing only Anomalies as requested
        filter_type = st.selectbox("Filter by Prediction", ["Anomaly", "All", "Normal"])
    with col_filter2:
        limit_rows = st.number_input("Limit Rows", min_value=100, max_value=10000, value=1000, step=100)
    
    # Custom query based on filters
    try:
        if not os.path.exists(DB_PATH):
            st.warning("Database not found yet.")
        else:
            conn = sqlite3.connect(DB_PATH)
            # Build query dynamically
            base_query = "SELECT * FROM anomalies"
            conditions = []
            params = []
            
            if filter_type == "Anomaly":
                conditions.append("prediction = 'Anomaly'")
            elif filter_type == "Normal":
                conditions.append("prediction = 'Normal'")
            # If "All", no condition added
                
            if conditions:
                base_query += " WHERE " + " AND ".join(conditions)
                
            # Add order and limit safely
            base_query += f" ORDER BY timestamp DESC LIMIT {limit_rows}"
            
            db_df = pd.read_sql_query(base_query, conn)
            conn.close()
            
            st.dataframe(db_df, use_container_width=True)
            
            # Download Button
            csv = db_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "Download Data as CSV",
                csv,
                "anomalies_db_export.csv",
                "text/csv",
                key='download-csv'
            )
            
            st.caption(f"Showing {len(db_df)} records from {DB_PATH}")
        
    except Exception as e:
        st.error(f"Error reading database: {e}")

st.sidebar.header("Settings")
refresh_rate = st.sidebar.slider("Refresh Rate (seconds)", 1, 60, 2)

if st.sidebar.button("Refresh Data Now"):
    st.rerun()

# Auto-refresh loop
while True:
    df, db_total_count, db_total_anomalies = load_data()
    
    if not df.empty:
        # --- Dashboard Logic ---
        # Current view stats (last 1000)
        view_total = len(df)
        view_anomalies = df[df['prediction'] == 'Anomaly']

        # Ensure 'velocity' column exists in df for visualization
        if 'velocity' not in df.columns:
            df['velocity'] = 0 # Default if column missing (e.g. old data)
            view_anomalies = df[df['prediction'] == 'Anomaly'] # Re-filter to include velocity column

        # Ratio based on total history
        ratio = (db_total_anomalies / db_total_count) * 100 if db_total_count > 0 else 0

        with metric_total.container():
            st.metric("Total Transactions (All Time)", db_total_count)
            
        with metric_anomalies.container():
            st.metric("Anomalies Detected (All Time)", db_total_anomalies, delta_color="inverse")
            
        with metric_ratio.container():
            st.metric("Anomaly Ratio", f"{ratio:.2f}%")

        # Visualization
        with chart_placeholder.container():
            col_chart1, col_chart2 = st.columns(2)
            
            with col_chart1:
                fig = px.scatter(
                    df, 
                    x="timestamp", 
                    y="amount", 
                    color="prediction", 
                    color_discrete_map={"Normal": "blue", "Anomaly": "red"},
                    title="Transaction Amount vs Time",
                    hover_data=["transaction_id", "location", "velocity"]
                )
                st.plotly_chart(fig, use_container_width=True)
                
            with col_chart2:
                # Velocity distribution
                # Ensure velocity is numeric
                df['velocity'] = pd.to_numeric(df['velocity'], errors='coerce').fillna(0)
                df['prediction'] = df['prediction'].astype(str).str.strip()
                
                # Robust approach: Aggregate manually before plotting
                # This avoids Plotly histogram binning issues
                velocity_counts = df.groupby(['velocity', 'prediction']).size().reset_index(name='count')
                
                # DEBUG: Show the data being plotted
                st.write("Debug - Plot Data:", velocity_counts)
                
                fig2 = px.bar(
                    velocity_counts,
                    x="velocity",
                    y="count",
                    # color="prediction", # Temporarily remove color to isolate issue
                    # color_discrete_map={"Normal": "#1f77b4", "Anomaly": "#ff7f0e"}, 
                    title="Transaction Velocity Distribution (Simple Bar)",
                    # log_y=True, # Temporarily remove log_y
                    opacity=0.8
                )
                
                # Force x-axis to show all integers if range is small, or let it scale
                # if df['velocity'].max() < 50:
                #    fig2.update_xaxes(dtick=1)
                
                st.plotly_chart(fig2, use_container_width=True, key="velocity_bar")

        # Recent Anomalies Table
        with table_placeholder.container():
            st.subheader("Recent Anomalies")
            if not view_anomalies.empty:
                st.dataframe(
                    view_anomalies[['timestamp', 'amount', 'location', 'velocity', 'transaction_id']].head(10), 
                    use_container_width=True
                )
            else:
                st.info("No anomalies detected in the recent stream.")
                
        # --- Live Stream Logic ---
        with live_table_placeholder.container():
            # Ensure it acts like a log stream (newest on top)
            
            # Show all transactions, highlighting anomalies
            def highlight_anomaly(row):
                color = '#ffcdd2' if row['prediction'] == 'Anomaly' else ''
                return [f'background-color: {color}' for _ in row]

            # Force re-render with a unique key if needed, but dataframe updates should be reactive
            st.dataframe(
                df[['timestamp', 'amount', 'location', 'velocity', 'prediction', 'transaction_id']].head(50)
                .style.apply(highlight_anomaly, axis=1),
                use_container_width=True,
                height=600  # Make it taller to look like a log feed
            )
            
    else:
        with metric_total.container():
            st.metric("Total Transactions", 0)
        with metric_anomalies.container():
            st.metric("Anomalies Detected", 0)
        with metric_ratio.container():
            st.metric("Anomaly Ratio", "0%")
            
        st.warning("Waiting for data... (Ensure Kafka and Spark are running)")
        
    time.sleep(refresh_rate)
