# AI Smart Timetable Planner

A beginner-friendly Flask + SQLite website that helps students organize study tasks and build a deadline-first timetable from their available study hours.

## Features
- Add subjects, topics, deadlines, estimated hours and priority.
- Add weekly available study-time windows.
- Generate a timetable using a simple deadline-first scheduling algorithm.
- Review tasks that still need more available time.
- Data is stored locally in SQLite.

## Run on MacBook Air M1
1. Install Python 3 if it is not already installed.
2. Open Terminal and move into this project folder.
3. Create a virtual environment:
   `python3 -m venv venv`
4. Activate it:
   `source venv/bin/activate`
5. Install packages:
   `pip install -r requirements.txt`
6. Start the website:
   `python app.py`
7. Open `http://127.0.0.1:5000` in your browser.

## Notes
This is a student project prototype. The timetable generator uses a simple rule-based planner (deadline first); it does not connect to an external AI service. You can extend it with break times, calendar export, and smarter workload balancing.
