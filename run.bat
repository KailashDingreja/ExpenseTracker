@echo off
cd /d "%~dp0"
if not exist .venv (
    python -m venv .venv
    .venv\Scripts\python -m pip install -q -e .
)
.venv\Scripts\streamlit run app.py
