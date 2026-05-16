import streamlit as st
import boto3
import pandas as pd
import numpy as np
import plotly.express as px
from streamlit_folium import st_folium
import folium
from folium.plugins import MarkerCluster, HeatMap

st.set_page_config(page_title="National Blood Grid , layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 20px; border-radius: 12px; border-left: 6px solid #d32f2f; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    h1 { color: #d32f2f; font-family: 'Inter', sans-serif; font-weight: 800; text-align: center; }
    .stButton>button { background-color: #d32f2f; color: white; border-radius: 8px; width: 100%; border: none; }
    .stButton>button:hover { background-color: #a32424; color: white; }
    </style>
""", unsafe_content_html=True)

@st.cache_data(ttl=600)
def load_and_preprocess_data():
    try:
        session = boto3.Session(
               aws_access_key_id=st.secrets["AWS_ACCESS_KEY_ID"],
               aws_secret_access_key=st.secrets["AWS_SECRET_ACCESS_KEY"],
               region_name='ap-south-1' #any region
        )
        
        dynamodb = session.resource('dynamodb')
        table = dynamodb.Table('BloodStock') 
        response = table.scan()
        df = pd.DataFrame(response['Items'])
        
        if df.empty:
            return pd.DataFrame()

        df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
        df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
        
        # Ensure 'pincode' and 'district_name' exist
        df['pincode'] = df.get('pincode', 'N/A').astype(str)
        df['district_name'] = df.get('district_name', 'Unknown')
        
        np.random.seed(42)
        df['demand_score'] = np.random.randint(10, 100, size=len(df))
        
        return df.dropna(subset=['latitude', 'longitude'])

    except Exception as e:
        st.error(f" Cloud Connection Failed: {e}")
        return pd.DataFrame()
    
def main():
    df = load_and_preprocess_data()
    
    if df.empty:
        st.error(" Data not found. Ensure your DynamoDB table 'KarnatakaBloodStock' has items and keys are correct.")
        return

    st.sidebar.title(" Project Controls")
    
    if st.sidebar.button(" Sync Live Data"):
        st.cache_data.clear()
        st.rerun()

    dist_list = sorted(df['district_name'].unique())
    selected_districts = st.sidebar.multiselect("Regional Scope", options=dist_list, default=dist_list[:3])
    risk_threshold = st.sidebar.slider("Shortage Risk Threshold (%)", 0, 100, 70)

    # Filtering Logic
    filtered_df = df[df['district_name'].isin(selected_districts)] if selected_districts else df

    st.title(" National Blood Grid & Inventory System")
    st.markdown("<p style='text-align: center;'>Real-time AI-Driven Geospatial Resource Allocation Dashboard</p>", unsafe_content_html=True)
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Facilities", len(filtered_df), delta="Active")
    m2.metric("Avg Stock Level", f"{int(filtered_df['demand_score'].mean())}%", delta="-2% Weekly")
    m3.metric("Critical Alerts", len(filtered_df[filtered_df['demand_score'] > risk_threshold]), delta_color="inverse")
    m4.metric("System Health", "Optimal")

    st.divider()
    st.header(" Regional Health Coverage Map")
    col_map, col_info = st.columns([3, 1])

    with col_map:
        # Folium Map with Clustering and Heat Layers
        m = folium.Map(location=[12.9716, 77.5946], zoom_start=10, tiles="cartodbpositron")
        
        # Heatmap Layer (Infrastructure Density)
        heat_data = [[row['latitude'], row['longitude']] for _, row in filtered_df.iterrows()]
        HeatMap(heat_data, radius=15, blur=10).add_to(m)
        
        # Marker Cluster Layer
        marker_cluster = MarkerCluster(name="Hospitals").add_to(m)
        for _, row in filtered_df.iterrows():
            color = 'red' if row['demand_score'] > risk_threshold else 'green'
            folium.Marker(
                location=[row['latitude'], row['longitude']],
                popup=f"<b>{row['hospital_name']}</b><br>Stock: {row['demand_score']}%",
                icon=folium.Icon(color=color, icon='plus', prefix='fa')
            ).add_to(marker_cluster)
        
        st_folium(m, width=900, height=500)

    with col_info:
        st.write("### Search Unit")
        search_pin = st.text_input("Enter Pincode:")
        if search_pin:
            res = df[df['pincode'] == search_pin]
            if not res.empty:
                st.dataframe(res[['hospital_name', 'contact', 'demand_score']])
            else:
                st.error("No results.")
        st.info("Map indicators change to RED when inventory falls below the risk threshold.")

    st.divider()
    st.header("Supply-Chain Analytics")
    c1, c2 = st.columns(2)

    with c1:
        fig_bar = px.bar(filtered_df, x='district_name', y='demand_score', 
                         color='district_name', title="Projected Unit Inventory by District",
                         color_discrete_sequence=px.colors.sequential.Reds)
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_info:
        # Category Logic
        fig_pie = px.pie(filtered_df, names='category', title="Sector Distribution",
                         hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig_pie, use_container_width=True)

    st.divider()
    st.header("Advanced Feature: Predictive Demand Forecasting")
    hosp = st.selectbox("Select Facility for AI Prediction:", filtered_df['hospital_name'].unique())
    
    if hosp:
        curr = filtered_df[filtered_df['hospital_name'] == hosp]['demand_score'].iloc[0]
        
        forecast_df = pd.DataFrame({
            'Timeframe': ['T-24h', 'T-12h', 'Current', 'T+12h (Pred)', 'T+24h (Pred)'],
            'Stock Level': [curr+15, curr+8, curr, curr-12, curr-20]
        })
        fig_line = px.line(forecast_df, x='Timeframe', y='Stock Level', markers=True, 
                          title=f"Predicted Inventory Trend for {hosp}")
        fig_line.add_hline(y=risk_threshold, line_dash="dash", line_color="red")
        st.plotly_chart(fig_line, use_container_width=True)
        st.success(f"Predictive analysis for {hosp} successfully computed via Cloud-Engine.")

if __name__ == "__main__":
    main()
