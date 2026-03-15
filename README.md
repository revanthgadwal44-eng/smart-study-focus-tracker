<<<<<<< HEAD
# Smart Study Focus Tracker

A full-stack study session tracker with analytics, gamification, and productivity insights.

## Stack

- **Frontend:** HTML, CSS, Vanilla JavaScript, Chart.js
- **Backend:** Python Flask
- **Database:** SQLite

## Features

1. **User Authentication** – Signup/Login with password hashing and session-based auth
2. **Study Session Tracker** – Subject selection, timer, notes, save to database
3. **Daily + Weekly Analytics** – Today hours, weekly hours, subject-wise totals
4. **Day Streak** – Consecutive days with study sessions
5. **Weekly Progress Bar** – Mon–Sun view, current day highlighted in blue
6. **Subject Breakdown Chart** – Pie chart (Chart.js)
7. **Focus Score** – `(totalMinutes * streak) / (distractions + 1)`
8. **Gamification** – XP (1/min), levels (every 500 XP), badges (3d Bronze, 7d Silver, 30d Gold)
9. **Smart Recommendations** – Weakest subject and daily focus suggestion
10. **Reports** – Download weekly PDF report
11. **Distraction Tracker** – Per-session distraction count
12. **Productivity Prediction** – Tomorrow’s study time from last 7-day average
13. **Notifications** – Browser reminder when no session today

## Project Structure

```
smart-study-tracker/
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js
├── backend/
│   ├── app.py
│   └── database.db       (created on first run)
├── requirements.txt
└── README.md
```

## Setup

### 1. Create virtual environment (recommended)

```bash
cd smart-study-tracker
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the application

```bash
cd backend
python app.py
```

The app runs at **http://127.0.0.1:5000**

### 4. First use

1. Open http://127.0.0.1:5000 in your browser
2. Click **Sign Up** and create an account
3. Log in and start tracking study sessions

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/signup` | Register |
| POST | `/api/auth/login` | Login |
| POST | `/api/auth/logout` | Logout |
| GET | `/api/auth/me` | Current user |
| GET | `/api/subjects` | List subjects |
| POST | `/api/subjects` | Add subject |
| GET | `/api/sessions` | List sessions |
| POST | `/api/sessions` | Create session |
| POST | `/api/sessions/<id>/distraction` | Add distraction |
| GET | `/api/analytics/daily` | Today’s minutes |
| GET | `/api/analytics/weekly` | Weekly totals |
| GET | `/api/analytics/streak` | Day streak |
| GET | `/api/analytics/weekly-progress` | Mon–Sun bars |
| GET | `/api/analytics/subject-breakdown` | Subject totals |
| GET | `/api/analytics/focus-score` | Focus score |
| GET | `/api/analytics/prediction` | Predicted tomorrow |
| GET | `/api/gamification` | XP, level, badges |
| GET | `/api/recommendations` | Smart suggestion |
| GET | `/api/reports/weekly-pdf` | Weekly PDF |
| GET | `/api/notifications/check` | Studied today? |

## Database Schema

**users** – id, username, email, password_hash, created_at  

**study_sessions** – id, user_id, subject, start_time, end_time, duration_minutes, notes, distractions, created_at  

**user_subjects** – id, user_id, subject_name  

## Production Notes

- Set `SECRET_KEY` environment variable in production
- Use a production WSGI server (e.g. Gunicorn)
- Enable HTTPS for session cookies
=======
# smart-study-focus-tracker
>>>>>>> 5b88dbf6d90e44b5f73f34d3c76cc29135867f5c
