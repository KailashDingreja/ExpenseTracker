# Ledgify

## Project Name

Ledgify — a personal expense tracker.

## Project Description

Ledgify is a local-first app for recording and reviewing personal income and expenses. It uses SQLite to store data on your computer; it does not require an account or send your financial data to a cloud service.

## Features

- Record, edit, delete, filter, and search income and expenses
- Organize transactions with customizable categories
- Set monthly budgets and review spending reports
- Import and export transactions as CSV
- Back up and restore your local database
- Customize currency, text size, and contrast

## Technology Used

- Python 3.11 or newer
- Streamlit
- SQLite
- pandas and Plotly
- Pydantic
- pytest (development and testing)

## How to Install

1. Install Python 3.11 or newer.
2. Clone the repository and change into the project directory:

   ```powershell
   git clone https://github.com/KailashDingreja/ExpenseTracker.git
   cd ExpenseTracker
   ```

3. Create and activate a virtual environment, then install the project:

   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   python -m pip install -e .
   ```

   To install the development dependencies (including pytest), use:

   ```powershell
   python -m pip install -e ".[dev]"
   ```

## How to Run Locally

From the project directory, start the app:

```powershell
streamlit run app.py
```

Then open [http://localhost:8501](http://localhost:8501) in your browser. On Windows, you can also double-click `run.bat`; it creates a virtual environment and installs the app on the first run.

By default, the database is stored at `%APPDATA%\Ledgify\ledgify.db` on Windows. Set `LEDGIFY_DATA_DIR` to use a different data directory. The database is not encrypted, so protect your local files and backups.

To run tests after installing the development dependencies:

```powershell
python -m pytest
```

## GitHub Repository

[https://github.com/KailashDingreja/ExpenseTracker](https://github.com/KailashDingreja/ExpenseTracker)

## Live Application URL

Not currently deployed. Run the app locally using the instructions above.
