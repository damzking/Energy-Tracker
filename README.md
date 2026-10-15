Africa Emissions Tracker
========================

A Streamlit dashboard for exploring EDGAR greenhouse gas emissions across countries, gas types, and sectors.

Local run
---------

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

Deployment-ready setup
----------------------

This project is prepared for standard Streamlit deployment environments.

Required files:
- `requirements.txt` — Python dependencies
- `app.py` — dashboard entry point
- `.streamlit/config.toml` — Streamlit server settings
- `Procfile` — optional host command for platforms like Render
- `runtime.txt` — Python version pin

Files included in the project:
- `app.py` — main dashboard
- `utils.py` — helper functions
- `data/GHG_totals_by_country.csv` — country totals export
- `EDGAR_2026_GHG_booklet_2026.xlsx` — source workbook

Deployment notes
----------------

For Streamlit Community Cloud:
1. Push this repository to GitHub.
2. Create a new app in Streamlit Cloud.
3. Select the repo and branch.
4. Use the default app path `app.py`.
5. Streamlit will install `requirements.txt` automatically.

For Render or similar platforms:
1. Connect the repo.
2. Set the build command to `pip install -r requirements.txt`.
3. Set the start command to `streamlit run app.py --server.address 0.0.0.0 --server.port $PORT`.

Important:
- The dashboard loads data from files in the project root, so the app must run from the repository root.
- The Excel workbook is required for the sector and gas tabs; keep it in the repo.
