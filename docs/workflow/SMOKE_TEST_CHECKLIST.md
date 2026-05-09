# SwissEdge Smoke Test Checklist

## Backend

From VPS:

    cd /opt/swissedge
    source .venv/bin/activate
    python -m alembic current
    curl -s http://127.0.0.1:8000/api/health/ping

## Frontend

Open:

- /
- /investment/evaluations
- /investment/research
- /investment/source-intelligence
- /investment/historical-cases

## Investment Research

Check:
- ResearchCase opens
- Brief saves
- Tasks save
- Documents save
- Sources save
- AI previews are manual only
- saved_to_db:false where expected
- No publishing
- No scanner trigger
