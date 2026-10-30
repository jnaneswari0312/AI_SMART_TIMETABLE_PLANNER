import streamlit as st
import pandas as pd
from datetime import time, datetime, timedelta
import random

st.set_page_config(page_title="AI Smart Timetable Planner", page_icon="📅", layout="wide")

st.title("📅 AI Smart Timetable Planner")
st.caption("Create a balanced weekly study timetable based on your subjects, priorities, available time, and study goals.")

with st.sidebar:
    st.header("⚙️ Planner settings")
    start_day = st.selectbox("Start your week on", ["Monday", "Sunday"])
    study_start = st.time_input("Daily study start time", value=time(17, 0))
    study_end = st.time_input("Daily study end time", value=time(21, 0))
    session_minutes = st.select_slider("Study session length", options=[25, 30, 45, 50, 60, 75, 90], value=50)
    break_minutes = st.select_slider("Break between sessions", options=[5, 10, 15, 20], value=10)
    max_daily_hours = st.slider("Maximum study hours per day", 1, 8, 4)
    include_weekend = st.checkbox("Include weekends", value=True)

st.subheader("1. Add your subjects")
st.write("Enter each subject, its priority, and the number of hours you want to study per week.")

if "subjects" not in st.session_state:
    st.session_state.subjects = [
        {"Subject": "Mathematics", "Priority": "High", "Hours per week": 4},
        {"Subject": "Computer Networks", "Priority": "High", "Hours per week": 3},
        {"Subject": "Python", "Priority": "Medium", "Hours per week": 3},
    ]

edited = st.data_editor(
    pd.DataFrame(st.session_state.subjects),
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "Subject": st.column_config.TextColumn("Subject", required=True),
        "Priority": st.column_config.SelectboxColumn("Priority", options=["High", "Medium", "Low"], required=True),
        "Hours per week": st.column_config.NumberColumn("Hours per week", min_value=1, max_value=30, step=1, required=True),
    },
    key="subject_editor",
)
st.session_state.subjects = edited.to_dict("records")

st.subheader("2. Choose your available days")
days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
if start_day == "Sunday":
    days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
default_days = days if include_weekend else days[:5]
available_days = st.multiselect("Select the days you can study", days, default=default_days)

st.subheader("3. Generate your timetable")
st.write("The planner distributes high-priority subjects first, avoids overloading a day, and inserts breaks between sessions.")

def generate_plan(subject_rows, chosen_days, start, end, session_len, break_len, daily_limit):
    valid = []
    for row in subject_rows:
        name = str(row.get("Subject", "")).strip()
        try:
            hours = float(row.get("Hours per week", 0))
        except (TypeError, ValueError):
            hours = 0
        priority = str(row.get("Priority", "Medium"))
        if name and hours > 0:
            valid.append({"name": name, "hours": hours, "priority": priority})

    if not valid or not chosen_days:
        return [], "Please add at least one subject and select at least one study day."
    if start >= end:
        return [], "The daily end time must be later than the start time."

    priority_weight = {"High": 3, "Medium": 2, "Low": 1}
    # Convert weekly hours to session-sized blocks. Round up so requested time is not silently lost.
    tasks = []
    for subject in valid:
        total_minutes = int(subject["hours"] * 60)
        count = max(1, (total_minutes + session_len - 1) // session_len)
        for _ in range(count):
            tasks.append({
                "subject": subject["name"],
                "priority": subject["priority"],
                "weight": priority_weight.get(subject["priority"], 2)
            })

    # Place higher-priority tasks first, then rotate subjects to avoid repetitive blocks.
    tasks.sort(key=lambda x: (x["weight"], random.random()), reverse=True)
    plan = []
    day_minutes = {day: 0 for day in chosen_days}
    day_slots = {day: [] for day in chosen_days}
    daily_cap = daily_limit * 60
    available_minutes = int((datetime.combine(datetime.today(), end) -
                             datetime.combine(datetime.today(), start)).total_seconds() // 60)

    # Round-robin over days while respecting the daily cap and available clock time.
    for task in tasks:
        placed = False
        for day in sorted(chosen_days, key=lambda d: (day_minutes[d], chosen_days.index(d))):
            used = day_minutes[day]
            needed = session_len + (break_len if day_slots[day] else 0)
            if used + needed <= min(daily_cap, available_minutes):
                slot_start = datetime.combine(datetime.today(), start) + timedelta(minutes=used)
                slot_end = slot_start + timedelta(minutes=session_len)
                day_slots[day].append({
                    "Day": day,
                    "Start": slot_start.strftime("%I:%M %p"),
                    "End": slot_end.strftime("%I:%M %p"),
                    "Subject": task["subject"],
                    "Priority": task["priority"],
                    "Duration (min)": session_len,
                    "Type": "Study"
                })
                day_minutes[day] += needed
                placed = True
                break
        if not placed:
            continue

    for day in chosen_days:
        plan.extend(day_slots[day])

    if not plan:
        return [], "No sessions could fit. Increase your available hours or reduce the daily study limit."
    return plan, None

if st.button("✨ Generate smart timetable", type="primary", use_container_width=True):
    plan, error = generate_plan(
        st.session_state.subjects, available_days, study_start, study_end,
        session_minutes, break_minutes, max_daily_hours
    )
    if error:
        st.error(error)
        st.session_state.pop("generated_plan", None)
    else:
        st.session_state.generated_plan = plan

if "generated_plan" in st.session_state:
    plan_df = pd.DataFrame(st.session_state.generated_plan)
    st.divider()
    st.subheader("📘 Your weekly timetable")
    tabs = st.tabs(["Weekly overview"] + available_days)
    with tabs[0]:
        pivot = plan_df.pivot_table(index="Start", columns="Day", values="Subject", aggfunc=lambda x: ", ".join(x), fill_value="")
        st.dataframe(pivot, use_container_width=True)
    for tab, day in zip(tabs[1:], available_days):
        with tab:
            day_df = plan_df[plan_df["Day"] == day][["Start", "End", "Subject", "Priority", "Duration (min)"]]
            if day_df.empty:
                st.info("No study sessions scheduled for this day.")
            else:
                st.dataframe(day_df, hide_index=True, use_container_width=True)

    st.subheader("📊 Study distribution")
    summary = plan_df.groupby("Subject")["Duration (min)"].sum().reset_index()
    summary["Hours"] = (summary["Duration (min)"] / 60).round(2)
    st.bar_chart(summary.set_index("Subject")["Hours"])
    st.dataframe(summary[["Subject", "Hours"]], hide_index=True, use_container_width=True)

    csv = plan_df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download timetable as CSV", csv, "smart_timetable.csv", "text/csv")
    st.success(f"Created {len(plan_df)} study sessions across {plan_df['Day'].nunique()} day(s).")

st.divider()
st.caption("Tip: Treat this as a suggested plan. Adjust it around classes, assignments, meals, and rest. This app uses a built-in scheduling algorithm and does not require an external AI API.")
