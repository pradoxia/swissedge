PYTHON = python
UVICORN = python -m uvicorn

.PHONY: dev test doctor ingest-course infra infra-down

infra:
	docker compose up -d

infra-down:
	docker compose down

dev:
	PYTHONPATH=. $(UVICORN) backend.main:app --reload --host 0.0.0.0 --port 8000

test:
	PYTHONPATH=. pytest backend/tests/ -v

doctor:
	PYTHONPATH=. $(PYTHON) scripts/doctor.py

ingest-course:
	PYTHONPATH=. $(PYTHON) scripts/ingest_course.py
