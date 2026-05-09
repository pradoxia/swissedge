# SwissEdge Deploy Checklist

Dani approval is required before running deploy or migration commands.

## Backend

Run from repo root:

    .\scripts\deploy_backend_files.ps1

## Frontend

Run from repo root:

    .\scripts\deploy_frontend.ps1

## Migrations

Only when explicitly approved:

    cd /opt/swissedge
    source .venv/bin/activate
    python -m alembic current
    python -m alembic upgrade <revision>

## Never Use Fake Deploy Notes

Do not use:
- Vercel auto-deploy
- git push as deploy
- systemctl swissedge-backend unless service name is verified
