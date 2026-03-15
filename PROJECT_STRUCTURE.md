# Smart Study Focus Tracker - Project Structure

## Improved Architecture (Post-Refactor)

```
smart-study-tracker/
├── backend/
│   ├── app.py                 # Flask app entry, blueprint registration
│   ├── database/
│   │   ├── __init__.py
│   │   └── db.py              # DB connection, schema init
│   ├── models/
│   │   └── __init__.py        # Data models (schema in db.py)
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py            # Signup, login, logout, me
│   │   ├── subjects.py        # CRUD subjects
│   │   ├── sessions.py        # Create/list sessions, distractions
│   │   ├── analytics.py       # Daily, weekly, streak, heatmap, dashboard (batched)
│   │   ├── gamification.py    # XP, level, badges
│   │   ├── recommendations.py # Weakest subject suggestion
│   │   ├── reports.py         # PDF generation
│   │   └── notifications.py   # Study reminder check
│   ├── services/
│   │   ├── __init__.py
│   │   └── analytics.py       # Shared streak/date logic
│   └── utils/
│       ├── __init__.py
│       ├── response.py        # success_response(), error_response()
│       └── validation.py      # Input validation
├── frontend/
│   ├── index.html
│   ├── app.js                 # Modular, batched API calls
│   └── style.css
├── venv/
├── requirements.txt
└── README.md
```

## Backend Improvements

- **Modular structure**: Routes in blueprints, DB in `database/`, shared logic in `services/`
- **Consistent API**: All responses `{ success: true, data: ... }` or `{ success: false, error: ... }`
- **User isolation**: Every query filters by `user_id` (session)
- **Validation**: Email, username, password, subject length and format
- **Batched analytics**: `/api/analytics/dashboard` returns all metrics in one request
- **Error handling**: Global 404/500 handlers, structured error responses

## Frontend Improvements

- **Subjects**: Add, Edit, Delete with proper event delegation (no inline onclick)
- **Analytics**: Uses batched `/api/analytics/dashboard` when available
- **Loading states**: Skeleton loaders for charts, heatmap, recommendations
- **XSS safety**: `escapeHtml()` used for user-controlled content
- **Single add-subject listener**: Removed duplicate handlers

## Run

```bash
cd backend
python app.py
# or: flask --app app run
```

Then open http://localhost:5000
