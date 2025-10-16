# studio_dashboard.py
# -------------------------------------
# Interactive Fitness Studio Dashboard
# -------------------------------------

import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

# ---------------------
# Load cleaned dataset
# ---------------------
@st.cache_data
def load_data():
    df = pd.read_csv("classes_cleaned.csv")
    df["StartDateTime"] = pd.to_datetime(df["StartDateTime"], errors="coerce")
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Weekday"] = pd.Categorical(
        df["Weekday"],
        categories=["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"],
        ordered=True
    )
    return df

df = load_data()

st.set_page_config(page_title="Studio Performance Dashboard", layout="wide")
st.title("🏋️ Areve Studio Performance Dashboard")

# ---------------------
# Sidebar Filters
# ---------------------
st.sidebar.header("Filters")

min_date, max_date = df["Date"].min(), df["Date"].max()
date_range = st.sidebar.date_input("Select Date Range:", [min_date, max_date])

discipline_list = ["All"] + sorted(df["Disciplina"].dropna().unique().tolist())
discipline = st.sidebar.selectbox("Discipline:", discipline_list)

instructor_list = ["All"] + sorted(df["Entrenador"].dropna().unique().tolist())
instructor = st.sidebar.selectbox("Instructor:", instructor_list)

# Apply filters
mask = (df["Date"] >= pd.to_datetime(date_range[0])) & (df["Date"] <= pd.to_datetime(date_range[1]))
if discipline != "All":
    mask &= (df["Disciplina"] == discipline)
if instructor != "All":
    mask &= (df["Entrenador"] == instructor)

filtered = df[mask].copy()

# ---------------------
# KPI Summary Section
# ---------------------
st.subheader("📈 Key Performance Indicators")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Classes", len(filtered))
col2.metric("Avg Occupancy %", f"{filtered['CapacityUtilization'].mean()*100:.1f}%")
col3.metric("Avg Booking Rate %", f"{filtered['BookingRate'].mean()*100:.1f}%")
col4.metric("Avg No-Show Rate %", f"{filtered['NoShowRate'].mean()*100:.1f}%")

# ---------------------
# Visualization Section
# ---------------------
st.markdown("### Average Occupancy by Discipline")
discipline_chart = (
    filtered.groupby("Disciplina", as_index=False)["CapacityUtilization"]
    .mean()
)
chart1 = (
    alt.Chart(discipline_chart)
    .mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5)
    .encode(
        x=alt.X("Disciplina:N", title="Discipline"),
        y=alt.Y("CapacityUtilization:Q", title="Avg Occupancy", axis=alt.Axis(format="%")),
        color="Disciplina:N",
        tooltip=["Disciplina", alt.Tooltip("CapacityUtilization", format=".0%")]
    )
    .properties(height=350)
)
st.altair_chart(chart1, use_container_width=True)

# Instructor performance
st.markdown("### 🧑‍🏫 Instructor Performance (Occupancy %)")
instructor_chart = (
    filtered.groupby("Entrenador", as_index=False)["CapacityUtilization"]
    .mean()
)
chart2 = (
    alt.Chart(instructor_chart)
    .mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5)
    .encode(
        x=alt.X("Entrenador:N", sort="-y", title="Instructor"),
        y=alt.Y("CapacityUtilization:Q", title="Avg Occupancy", axis=alt.Axis(format="%")),
        color="Entrenador:N",
        tooltip=["Entrenador", alt.Tooltip("CapacityUtilization", format=".0%")]
    )
    .properties(height=350)
)
st.altair_chart(chart2, use_container_width=True)

# Hourly trend
st.markdown("### ⏰ Attendance by Hour of Day")
hour_chart = (
    filtered.groupby("Hour", as_index=False)["CapacityUtilization"]
    .mean()
)
chart3 = (
    alt.Chart(hour_chart)
    .mark_line(point=True)
    .encode(
        x=alt.X("Hour:O", title="Hour of Day"),
        y=alt.Y("CapacityUtilization:Q", title="Avg Occupancy", axis=alt.Axis(format="%")),
        tooltip=["Hour", alt.Tooltip("CapacityUtilization", format=".0%")]
    )
    .properties(height=300)
)
st.altair_chart(chart3, use_container_width=True)

# Weekday trend
st.markdown("### 📅 Attendance by Weekday")
weekday_chart = (
    filtered.groupby("Weekday", as_index=False)["CapacityUtilization"]
    .mean()
)
chart4 = (
    alt.Chart(weekday_chart)
    .mark_line(point=True, strokeDash=[3,2])
    .encode(
        x=alt.X("Weekday:N", sort=["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]),
        y=alt.Y("CapacityUtilization:Q", title="Avg Occupancy", axis=alt.Axis(format="%")),
        tooltip=["Weekday", alt.Tooltip("CapacityUtilization", format=".0%")]
    )
    .properties(height=300)
)
st.altair_chart(chart4, use_container_width=True)

# ---------------------
# Table Section
# ---------------------
st.markdown("### 📋 Detailed Data Preview")
st.dataframe(filtered[[
    "Date","Disciplina","Entrenador","Hour","Capacity","Bookings","Attended","NoShows",
    "CapacityUtilization","BookingRate","NoShowRate"
]].round(2))

st.caption("Data source: classes_cleaned.csv — updated automatically when new sessions are added.")
