from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import datetime, date, timedelta
from pathlib import Path

app = Flask(__name__)
app.secret_key = "change-this-secret-key"
DB = Path(__file__).with_name("timetable.db")

def connect():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with connect() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            topic TEXT NOT NULL,
            deadline TEXT NOT NULL,
            hours REAL NOT NULL,
            priority TEXT NOT NULL DEFAULT 'Medium'
        )""")
        con.execute("""CREATE TABLE IF NOT EXISTS availability (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            day TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL
        )""")

@app.route("/")
def index():
    with connect() as con:
        tasks = con.execute("SELECT * FROM tasks ORDER BY deadline").fetchall()
        slots = con.execute("SELECT * FROM availability ORDER BY id DESC").fetchall()
    return render_template("index.html", tasks=tasks, slots=slots, today=date.today().isoformat())

@app.post("/add-task")
def add_task():
    subject = request.form.get("subject", "").strip()
    topic = request.form.get("topic", "").strip()
    deadline = request.form.get("deadline", "")
    try:
        hours = float(request.form.get("hours", "0"))
    except ValueError:
        hours = 0
    priority = request.form.get("priority", "Medium")
    if not subject or not topic or not deadline or hours <= 0:
        flash("Please enter all task details and a valid study duration.")
    else:
        with connect() as con:
            con.execute("INSERT INTO tasks(subject, topic, deadline, hours, priority) VALUES(?,?,?,?,?)",
                        (subject, topic, deadline, hours, priority))
        flash("Study task added!")
    return redirect(url_for("index"))

@app.post("/add-availability")
def add_availability():
    day = request.form.get("day", "")
    start = request.form.get("start_time", "")
    end = request.form.get("end_time", "")
    if not day or not start or not end or start >= end:
        flash("Choose a day and a valid time range.")
    else:
        with connect() as con:
            con.execute("INSERT INTO availability(day,start_time,end_time) VALUES(?,?,?)", (day,start,end))
        flash("Available time saved!")
    return redirect(url_for("index"))

@app.post("/delete-task/<int:task_id>")
def delete_task(task_id):
    with connect() as con:
        con.execute("DELETE FROM tasks WHERE id=?", (task_id,))
    return redirect(url_for("index"))

@app.post("/delete-slot/<int:slot_id>")
def delete_slot(slot_id):
    with connect() as con:
        con.execute("DELETE FROM availability WHERE id=?", (slot_id,))
    return redirect(url_for("index"))

@app.route("/generate")
def generate():
    with connect() as con:
        tasks = con.execute("SELECT * FROM tasks ORDER BY deadline, CASE priority WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 ELSE 3 END").fetchall()
        slots = con.execute("SELECT * FROM availability ORDER BY day,start_time").fetchall()
    plan = []
    remaining = {t["id"]: float(t["hours"]) for t in tasks}
    # A simple deadline-first planner. Each availability window is divided into 1-hour blocks.
    for slot in slots:
        start = datetime.strptime(slot["start_time"], "%H:%M")
        end = datetime.strptime(slot["end_time"], "%H:%M")
        cursor = start
        while cursor + timedelta(hours=1) <= end:
            chosen = next((t for t in tasks if remaining[t["id"]] > 0 and t["deadline"] >= date.today().isoformat()), None)
            if not chosen:
                break
            plan.append({
                "day": slot["day"], "start": cursor.strftime("%I:%M %p"),
                "end": (cursor + timedelta(hours=1)).strftime("%I:%M %p"),
                "subject": chosen["subject"], "topic": chosen["topic"],
                "priority": chosen["priority"]
            })
            remaining[chosen["id"]] -= 1
            cursor += timedelta(hours=1)
    unscheduled = [t for t in tasks if remaining[t["id"]] > 0]
    return render_template("schedule.html", plan=plan, unscheduled=unscheduled)

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
