# studio_dashboard.py
# -------------------------------------
# Interactive Fitness Studio Dashboard (with Passcode)
# -------------------------------------

import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

# ---------------------
# Passcode Protection (Session State)
# ---------------------
import streamlit as st

st.set_page_config(page_title="Studio Performance Dashboard", layout="wide")

# Try to read passcode from secrets; fallback to default
try:
    PASSCODE = st.secrets["DASH_PASS"]
except Exception:
    PASSCODE = "areve123"  # fallback default

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

def _login():
    if st.session_state._pass_try == PASSCODE:
        st.session_state.authenticated = True
        # rerun for both new and older Streamlit versions
        if hasattr(st, "rerun"):
            st.rerun()
        else:
            st.experimental_rerun()

st.title("🔒 Secure Access - Areve Studio Dashboard")

if not st.session_state.authenticated:
    st.text_input(
        "Enter passcode to access the dashboard:",
        type="password",
        key="_pass_try",
        on_change=_login
    )
    # If user typed something wrong, show an error
    if st.session_state.get("_pass_try"):
        st.error("❌ Incorrect passcode. Please try again.")
    st.stop()

# Optional: logout
if st.sidebar.button("Log out"):
    st.session_state.clear()
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()



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



## Scorecards

st.markdown("### 🧑‍🏫 Instructor Scorecards")
score = (
    filtered.groupby("Entrenador", as_index=False)
    .agg(AvgOcc=("CapacityUtilization","mean"),
         AvgNoShow=("NoShowRate","mean"),
         N=("CapacityUtilization","size"))
)
st.dataframe(score.sort_values(["AvgOcc","N"], ascending=[False,False]).style.format({
    "AvgOcc":"{:.0%}", "AvgNoShow":"{:.0%}"
}))



#Heatmap test
# ==== Heatmaps with min-classes filter (robust) ====
st.markdown("### 🔥 Heatmaps (min class threshold)")

if filtered.empty:
    st.info("No classes match the current filters. Adjust filters to view heatmaps.")
else:
    # Ensure proper types/order
    if "Weekday" in filtered.columns:
        filtered["Weekday"] = pd.Categorical(
            filtered["Weekday"],
            categories=["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"],
            ordered=True
        )
    if "Hour" in filtered.columns:
        # keep numeric hours clean for grouping/axis
        filtered["Hour"] = pd.to_numeric(filtered["Hour"], errors="coerce")

    # Sidebar control for heatmap threshold
    with st.sidebar.expander("Heatmap settings"):
        MIN_CLASSES_HEAT = st.number_input(
            "Min classes per Weekday×Hour cell",
            min_value=1, value=3, step=1
        )

    def _heat_df(df, value_col, min_n):
        """Aggregate by Weekday×Hour; keep only cells with at least min_n classes."""
        need_cols = {"Weekday", "Hour", value_col}
        if not need_cols.issubset(df.columns):
            return None

        d = df.dropna(subset=["Weekday","Hour", value_col]).copy()

        # Group with observed=True to avoid expanding to all category levels
        g = d.groupby(["Weekday","Hour"], observed=True)

        # Compute mean and size separately to avoid pandas named-agg bug
        mean_df = g[value_col].mean().reset_index(name="value")
        size_df = g.size().reset_index(name="n")

        out = mean_df.merge(size_df, on=["Weekday","Hour"], how="inner")
        out = out.query("n >= @min_n")

        # Make Hour nice for display (optional)
        if "Hour" in out.columns:
            try:
                out["Hour"] = out["Hour"].astype(int)
            except Exception:
                pass
        return out

    # ---- Occupancy heatmap ----
    st.markdown("#### Avg Occupancy by Weekday × Hour")
    occ_df = _heat_df(filtered, "CapacityUtilization", MIN_CLASSES_HEAT)
    if occ_df is None or occ_df.empty:
        st.caption("Not enough data for occupancy heatmap with the current threshold.")
    else:
        chart_occ = alt.Chart(occ_df).mark_rect().encode(
            x=alt.X("Hour:O", title="Hour"),
            y=alt.Y("Weekday:N", sort=["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]),
            color=alt.Color("value:Q", title="Avg Occupancy", scale=alt.Scale(domain=[0,1])),
            tooltip=[
                alt.Tooltip("Weekday:N"),
                alt.Tooltip("Hour:O", title="Hour"),
                alt.Tooltip("value:Q", title="Avg Occupancy", format=".0%"),
                alt.Tooltip("n:Q", title="# Classes")
            ]
        ).properties(height=260)
        st.altair_chart(chart_occ, use_container_width=True)

    # ---- No-show heatmap ----
    st.markdown("#### Avg No-Show by Weekday × Hour")
    ns_df = _heat_df(filtered, "NoShowRate", MIN_CLASSES_HEAT)
    if ns_df is None or ns_df.empty:
        st.caption("Not enough data for no-show heatmap with the current threshold.")
    else:
        chart_ns = alt.Chart(ns_df).mark_rect().encode(
            x=alt.X("Hour:O", title="Hour"),
            y=alt.Y("Weekday:N", sort=["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]),
            color=alt.Color("value:Q", title="Avg No-Show", scale=alt.Scale(domain=[0,1])),
            tooltip=[
                alt.Tooltip("Weekday:N"),
                alt.Tooltip("Hour:O", title="Hour"),
                alt.Tooltip("value:Q", title="Avg No-Show", format=".0%"),
                alt.Tooltip("n:Q", title="# Classes")
            ]
        ).properties(height=260)
        st.altair_chart(chart_ns, use_container_width=True)


# ---------------------
# Table Section
# ---------------------
st.markdown("### 📋 Detailed Data Preview")
st.dataframe(filtered[[
    "Date","Disciplina","Entrenador","Hour","Capacity","Bookings","Attended","NoShows",
    "CapacityUtilization","BookingRate","NoShowRate"
]].round(2))

st.caption("Data source: classes_cleaned.csv — updated automatically when new sessions are added.")
