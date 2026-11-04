# CRM API

Небольшой учебный CRM API на FastAPI, SQLAlchemy и SQLite.

## Запуск

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

Документация API доступна по адресу http://127.0.0.1:8000/docs. База `database.db` создаётся рядом с проектом.

## Демо-данные

После установки зависимостей запустите `python seed_data.py`. Скрипт добавит недостающие записи до 20 пользователей, клиентов и задач; повторный запуск не дублирует демо-данные. Статусы задач: `pending`, `in_progress`, `completed`.
