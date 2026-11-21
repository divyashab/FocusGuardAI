
import streamlit as st
import pandas as pd
from pathlib import Path

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="FocusGuard AI",
    page_icon="🎯",
    layout="wide"
)

# ---------------- DESIGN ----------------
st.markdown("""
<style>
.stApp {
    background-color: #0b1020;
    color: #f1f5f9;
}
[data-testid="stSidebar"] {
    background-color: #11182b;
    border-right: 1px solid #26324a;
}
.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
}
h1, h2, h3 {
    color: #f8fafc !important;
}
div[data-testid="stMetric"] {
    background-color: #151e33;
    border: 1px solid #293550;
    padding: 18px;
    border-radius: 16px;
}
div[data-testid="stMetricLabel"] {
    color: #a5b4fc !important;
}
div[data-testid="stMetricValue"] {
    color: white !important;
}
</style>
""", unsafe_allow_html=True)

# ---------------- DATA PATH ----------------
DATA_PATH = Path(__file__).parent / "data" / "session_history.csv"

REQUIRED_COLUMNS = [
    "Date",
    "Total Session (seconds)",
    "Focus Time (seconds)",
    "Distraction Time (seconds)",
    "Distraction Events",
    "Focus Score (%)",
    "Completed Pomodoros"
]

NUMERIC_COLUMNS = REQUIRED_COLUMNS[1:]


# ---------------- LOAD DATA ----------------
def load_data():
    if not DATA_PATH.exists():
        return pd.DataFrame(columns=REQUIRED_COLUMNS)

    try:
        data = pd.read_csv(DATA_PATH)

        if data.empty:
            return pd.DataFrame(columns=REQUIRED_COLUMNS)

        # Add missing columns if needed
        for column in REQUIRED_COLUMNS:
            if column not in data.columns:
                data[column] = 0

        # Convert date
        data["Date"] = pd.to_datetime(
            data["Date"], errors="coerce"
        )

        # Convert numerical columns
        for column in NUMERIC_COLUMNS:
            data[column] = pd.to_numeric(
                data[column], errors="coerce"
            ).fillna(0)

        # Remove rows with invalid dates
        data = data.dropna(subset=["Date"])

        # Prevent negative values
        for column in [
            "Total Session (seconds)",
            "Focus Time (seconds)",
            "Distraction Time (seconds)",
            "Distraction Events",
            "Completed Pomodoros"
        ]:
            data[column] = data[column].clip(lower=0)

        # Focus score should be between 0 and 100
        data["Focus Score (%)"] = data[
            "Focus Score (%)"
        ].clip(0, 100)

        # Mark valid sessions
        data["Valid Session"] = (
            data["Total Session (seconds)"] > 0
        )

        return data.sort_values(
            "Date", ascending=False
        ).reset_index(drop=True)

    except Exception as error:
        st.error(f"CSV loading error: {error}")
        return pd.DataFrame(columns=REQUIRED_COLUMNS)


df = load_data()


# ---------------- FORMAT TIME ----------------
def format_time(seconds):
    seconds = max(0, int(seconds or 0))

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    remaining_seconds = seconds % 60

    if hours > 0:
        return f"{hours}h {minutes}m"

    if minutes > 0:
        return f"{minutes}m {remaining_seconds}s"

    return f"{remaining_seconds}s"


# ---------------- SMART INSIGHTS ----------------
def generate_insight(score, events, focus_minutes):

    if score >= 85:
        message = "Excellent focus! You're building a strong study habit."

    elif score >= 70:
        message = "Good work! You're maintaining a productive focus level."

    elif score >= 50:
        message = "Not bad. Try reducing distractions in your next session."

    else:
        message = "Try a shorter study session and remove distractions around you."

    if events >= 10:
        tip = "You had many distraction events. Try keeping your phone away."

    elif focus_minutes < 15:
        tip = "Try a longer uninterrupted focus block next time."

    else:
        tip = "Keep your study space calm and continue your momentum."

    return message, tip


# ---------------- SIDEBAR ----------------
with st.sidebar:

    st.title("🎯 FocusGuard AI")
    st.caption("Your personal focus companion")
    st.divider()

    page = st.radio(
        "Navigation",
        ["Overview", "Analytics", "Session History"]
    )

    st.divider()

    st.subheader("🧠 About FocusGuard")

    st.caption(
        "FocusGuard estimates screen-facing behavior "
        "using webcam-based head pose detection."
    )

    st.caption(
        "It tracks focus time, distractions and study sessions."
    )

    st.divider()
    st.caption("Stay consistent. Stay focused.")


# ---------------- NO DATA ----------------
if df.empty:

    st.title("🎯 FocusGuard AI")
    st.header("Your focus journey starts here!")

    st.info(
        "No saved sessions found yet. Your dashboard "
        "will display analytics after your first session."
    )

    st.subheader("How to record your first session")

    st.markdown("""
    1. Open the project in VS Code.
    2. Activate your virtual environment.
    3. Run `python src/main.py`.
    4. Start your study session.
    5. Press `Q` to end and save.
    6. Return here and refresh the dashboard.
    """)

    col1, col2, col3 = st.columns(3)

    col1.metric("Focus Time", "—")
    col2.metric("Distraction Events", "—")
    col3.metric("Focus Score", "—")

    st.stop()


# ---------------- DATE FILTER ----------------
with st.sidebar:

    st.subheader("📅 Filter by Date")

    min_date = df["Date"].min().date()
    max_date = df["Date"].max().date()

    date_range = st.date_input(
        "Session date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )


# ---------------- FILTER DATA ----------------
filtered_df = df.copy()

if isinstance(date_range, (tuple, list)) and len(date_range) == 2:

    start_date, end_date = date_range

    filtered_df = filtered_df[
        filtered_df["Date"].dt.date.between(
            start_date, end_date
        )
    ]

elif hasattr(date_range, "year"):

    filtered_df = filtered_df[
        filtered_df["Date"].dt.date == date_range
    ]


# Only count sessions with actual duration
valid_df = filtered_df[
    filtered_df["Valid Session"]
].copy()

session_count = len(valid_df)

focus_seconds = valid_df["Focus Time (seconds)"].sum()
distraction_seconds = valid_df["Distraction Time (seconds)"].sum()
distraction_events = valid_df["Distraction Events"].sum()
pomodoros = valid_df["Completed Pomodoros"].sum()

average_focus_score = (
    valid_df["Focus Score (%)"].mean()
    if session_count > 0 else 0
)

latest_session = (
    valid_df.iloc[0]
    if session_count > 0 else None
)


# ==================================================
# OVERVIEW
# ==================================================
if page == "Overview":

    st.title("📊 Focus Overview")
    st.caption("Your productivity at a glance.")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Average Focus Score",
        f"{average_focus_score:.1f}%"
    )

    col2.metric(
        "Total Focus Time",
        format_time(focus_seconds)
    )

    col3.metric(
        "Distraction Events",
        int(distraction_events)
    )

    col4.metric(
        "Pomodoros Completed",
        int(pomodoros)
    )

    st.divider()

    # Latest session
    st.subheader("✨ Latest Session")

    if latest_session is not None:

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Date",
            latest_session["Date"].strftime("%d %b %Y")
        )

        col2.metric(
            "Duration",
            format_time(
                latest_session["Total Session (seconds)"]
            )
        )

        col3.metric(
            "Focus Score",
            f"{latest_session['Focus Score (%)']:.1f}%"
        )

    else:
        st.info("No completed sessions available.")

    st.divider()

    # Focus versus distraction chart
    st.subheader("⏱️ Focus vs Distraction")

    if session_count > 0:

        chart_data = pd.DataFrame({
            "Category": ["Focus", "Distraction"],
            "Minutes": [
                focus_seconds / 60,
                distraction_seconds / 60
            ]
        })

        st.bar_chart(
            chart_data.set_index("Category")
        )

    else:
        st.info("Record a session to view this chart.")

    st.divider()

    # Recent sessions
    st.subheader("🗂️ Recent Sessions")

    if session_count > 0:

        recent = valid_df.head(5)[[
            "Date",
            "Total Session (seconds)",
            "Focus Score (%)",
            "Distraction Events",
            "Completed Pomodoros"
        ]].copy()

        recent["Date"] = recent["Date"].dt.strftime(
            "%d %b %Y"
        )

        recent["Total Session (seconds)"] = (
            recent["Total Session (seconds)"
            ].apply(format_time)
        )

        st.dataframe(
            recent,
            width="stretch",
            hide_index=True
        )

    else:
        st.info("No saved sessions to display.")

    st.divider()

    # Smart Focus Insights
    st.subheader("🧠 Smart Focus Insights")

    if session_count > 0:

        message, tip = generate_insight(
            average_focus_score,
            distraction_events,
            focus_seconds / 60
        )

        st.info(message)

        st.markdown("### 💡 Your Next-Session Tip")

        st.success(tip)

        st.caption(
            "Recommendations are generated using rule-based "
            "analysis of your recorded sessions."
        )

    else:
        st.info(
            "Insights will appear after you complete "
            "a tracking session."
        )


# ==================================================
# ANALYTICS
# ==================================================
elif page == "Analytics":

    st.title("📈 Focus Analytics")
    st.caption("Explore your focus patterns across sessions.")

    col1, col2 = st.columns(2)

    col1.metric("Sessions Analyzed", session_count)

    col2.metric(
        "Average Focus Score",
        f"{average_focus_score:.1f}%"
    )

    st.divider()

    st.subheader("Focus Score Trend")

    if session_count > 0:

        score_data = (
            valid_df.sort_values("Date")
            .set_index("Date")["Focus Score (%)"]
        )

        st.line_chart(score_data)

    else:
        st.info("No session data available.")

    st.divider()

    st.subheader("Focus & Distraction Over Time")

    if session_count > 0:

        time_data = (
            valid_df.sort_values("Date")
            .set_index("Date")[[
                "Focus Time (seconds)",
                "Distraction Time (seconds)"
            ]]
        ) / 60

        time_data.columns = [
            "Focus (minutes)",
            "Distraction (minutes)"
        ]

        st.line_chart(time_data)

    else:
        st.info("No session data available.")

    st.divider()

    st.subheader("Distraction Events per Session")

    if session_count > 0:

        event_data = (
            valid_df.sort_values("Date")
            .set_index("Date")["Distraction Events"]
        )

        st.bar_chart(event_data)

    else:
        st.info("No session data available.")


# ==================================================
# SESSION HISTORY
# ==================================================
elif page == "Session History":

    st.title("📚 Session History")
    st.caption("Review your previous study sessions.")

    st.metric("Total Completed Sessions", session_count)

    if session_count > 0:

        history = valid_df.copy()

        history["Date"] = history["Date"].dt.strftime(
            "%d %b %Y"
        )

        for column in NUMERIC_COLUMNS[:3]:

            history[column] = (
                history[column].apply(format_time)
            )

        history = history.rename(columns={
            "Total Session (seconds)": "Session Duration",
            "Focus Time (seconds)": "Focus Time",
            "Distraction Time (seconds)": "Distraction Time"
        })

        st.dataframe(
            history,
            width="stretch",
            hide_index=True
        )

        st.divider()

        csv_file = filtered_df.drop(
            columns=["Valid Session"],
            errors="ignore"
        ).to_csv(index=False).encode("utf-8")

        st.download_button(
            label="⬇️ Download Session Data",
            data=csv_file,
            file_name="focusguard_session_history.csv",
            mime="text/csv"
        )

    else:
        st.info("No sessions found for this date range.")


# ---------------- FOOTER ----------------
st.divider()

st.markdown(
    """
    <div style="text-align:center; color:#94a3b8;">
        🎯 FocusGuard AI • Stay consistent. Stay focused. Keep improving.
    </div>
    """,
    unsafe_allow_html=True
)
