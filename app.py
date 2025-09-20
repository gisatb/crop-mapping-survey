import streamlit as st
import leafmap.foliumap as leafmap
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import datetime
import random

st.set_page_config(page_title="Crop Mapping Validation Dashboard", layout="wide")
st.title("🌾 Crop Mapping & Ground Truth Validation Dashboard")
st.markdown("Validate crop classification using ground truth survey points and NDVI values.")

# -------------------
# 1. Simulate survey / ground truth points
crops = ["Wheat", "Rice", "Maize", "Soybean", "Sugarcane"]
status_options = ["Planted", "Harvested", "Field Visit Done", "Pending"]

data = []
for i in range(200):
    data.append({
        "Field_ID": f"F{i+1:03d}",
        "Crop": random.choice(crops),
        "Survey_Status": random.choice(status_options),
        "Survey_Date": datetime(2025, random.randint(1, 8), random.randint(1,28)),
        "Latitude": random.uniform(20.0, 23.0),
        "Longitude": random.uniform(75.0, 77.0),
        # Simulate NDVI and classified crop for validation
        "NDVI": round(random.uniform(0.2, 0.9), 2),
        "Classified_Crop": random.choice(crops),
        "Farmer_Name": f"Farmer_{i+1}"
    })

df = pd.DataFrame(data)

# -------------------
# Sidebar filters
st.sidebar.header("🔎 Filters")
selected_crops = st.sidebar.multiselect("Select Survey Crop(s)", options=crops, default=crops)
selected_status = st.sidebar.multiselect("Survey Status", options=status_options, default=status_options)
start_date = st.sidebar.date_input("Start Date", df["Survey_Date"].min())
end_date = st.sidebar.date_input("End Date", df["Survey_Date"].max())
ndvi_min = st.sidebar.slider("Minimum NDVI", 0.0, 1.0, 0.3, 0.01)
ndvi_max = st.sidebar.slider("Maximum NDVI", 0.0, 1.0, 1.0, 0.01)
show_only_match = st.sidebar.checkbox("Show only matching classified crops", value=False)

# Apply filters
mask = (
    (df["Crop"].isin(selected_crops)) &
    (df["Survey_Status"].isin(selected_status)) &
    (df["Survey_Date"].dt.date >= start_date) &
    (df["Survey_Date"].dt.date <= end_date) &
    (df["NDVI"] >= ndvi_min) &
    (df["NDVI"] <= ndvi_max)
)
if show_only_match:
    mask &= (df["Crop"] == df["Classified_Crop"])

filtered_df = df[mask]
st.sidebar.write(f"✅ Showing {len(filtered_df)} survey points after filters")

# -------------------
# Map
st.subheader("🗺️ Crop Survey Map & Classification Validation")
m = leafmap.Map(center=[21.5, 76], zoom=6)
if not filtered_df.empty:
    m.add_points_from_xy(
        filtered_df,
        x="Longitude",
        y="Latitude",
        popup=["Field_ID", "Crop", "Classified_Crop", "Survey_Status", "Survey_Date", "NDVI", "Farmer_Name"],
        layer_name="Survey Points",
        radius=5,
        fill_color="green",
        clustered=True
    )
    # Simulate NDVI raster layer as colored points or heatmap
    m.add_heatmap(
        filtered_df,
        latitude="Latitude",
        longitude="Longitude",
        value="NDVI",
        name="NDVI Heatmap",
        radius=20,
        blur=25
    )
m.to_streamlit(height=500)

# -------------------
# Data Table
st.subheader("📊 Survey & Classification Data Table")
st.dataframe(filtered_df.sort_values(by="Survey_Date", ascending=False))

# -------------------
# Download filtered data
st.subheader("💾 Download Filtered Data")
csv = filtered_df.to_csv(index=False)
st.download_button(
    label="Download CSV",
    data=csv,
    file_name="crop_survey_validation.csv",
    mime="text/csv"
)

# -------------------
# Statistics
st.subheader("📈 Summary Statistics")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Survey Points", len(filtered_df))
col2.metric("Unique Fields", filtered_df["Field_ID"].nunique())
col3.metric("Matching Crop Points", len(filtered_df[filtered_df["Crop"]==filtered_df["Classified_Crop"]]))
col4.metric("Average NDVI", round(filtered_df["NDVI"].mean(),2) if not filtered_df.empty else 0.0)

# -------------------
# Charts
st.subheader("📊 Charts for Validation")
if not filtered_df.empty:
    # 1. Crop Distribution
    fig1 = px.pie(filtered_df, names="Crop", title="Survey Crop Distribution")
    st.plotly_chart(fig1, use_container_width=True)

    # 2. Classified vs Survey Crop Match
    match_df = filtered_df.copy()
    match_df["Match"] = np.where(match_df["Crop"]==match_df["Classified_Crop"], "Yes", "No")
    fig2 = px.bar(match_df, x="Match", title="Survey vs Classified Crop Match Count")
    st.plotly_chart(fig2, use_container_width=True)

    # 3. NDVI Distribution by Crop
    fig3 = px.box(filtered_df, x="Crop", y="NDVI", title="NDVI Distribution per Crop")
    st.plotly_chart(fig3, use_container_width=True)

    # 4. Survey Timeline
    df_time = filtered_df.groupby(filtered_df["Survey_Date"].dt.date).size().reset_index(name="Count")
    fig4 = px.line(df_time, x="Survey_Date", y="Count", title="Survey Points Over Time")
    st.plotly_chart(fig4, use_container_width=True)
else:
    st.info("No data available for the selected filters.")
