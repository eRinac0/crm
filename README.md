# CRM API

Little CRM API on FastAPI, SQLAlchemy и SQLite.

## Launch

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

Domenys API - http://127.0.0.1:8000/docs. Base `database.db` create near the project



After installing the dependencies, run `python seed_data.py`. The script will add any missing records for up to 20 users, clients, and tasks; running it again will not duplicate the demo data. Task statuses: `pending`, `in_progress`, `completed`.
