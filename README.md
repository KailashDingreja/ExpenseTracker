# Ledgify

A private, local-first expense tracker. Streamlit + SQLite, one user, no login, no cloud.

## Run (Windows)

Double-click `run.bat`, or:

```powershell
python -m venv .venv
.venv\Scripts\pip install -e .[dev]
.venv\Scripts\streamlit run app.py
```

The app opens at http://localhost:8501.

## Where is my data?

`%APPDATA%\Ledgify\ledgify.db`. Set `LEDGIFY_DATA_DIR` to use another folder.
Use **Settings → Back up now** regularly. The data file is not encrypted.

## Tests

```powershell
.venv\Scripts\pytest
```

## Layout

See `plan.md`. Pages are in `pages/`, logic in `ledgify/` (db, repositories, services, ui).
