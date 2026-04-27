# ChittyScore

ChittyScore is the ChittyOS behavioral trust scoring service. The root of this repository is the canonical Python service surface.

## Canonical Service Boundary

The root service consists of:

- `app.py`: Flask API and trust engine wiring
- `main.py`: local entrypoint
- `src/chitty_score/`: scoring models, dimensions, and analytics
- `schema.sql`: database bootstrap material
- `requirements.txt` and `pyproject.toml`: Python packaging metadata

This repository also contains nested sub-projects such as `chittyfinance/`, `chittyassets/`, `chittypm/`, and `chitty-frontend/`. Those are independent projects and are not part of the root ChittyScore service runtime.

## Requirements

- Python `3.11+`
- PostgreSQL-compatible `DATABASE_URL` for persistence if database-backed flows are used

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

Or with Gunicorn:

```bash
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
```

## API Surface

- `GET /`
- `GET /api/health`
- `POST /api/trust/calculate`
- `GET /api/trust/demo/<persona_id>`

## Validation

Minimal static validation:

```bash
python -m py_compile app.py main.py src/chitty_score/*.py
```

Smoke test:

```bash
python -m unittest tests.test_smoke
```

## Notes

- `ChittyTrust` is the cryptographic root authority. `ChittyScore` is the behavioral scoring layer.
- Root packaging and deployment should target the Python service only.
- Nested applications should be validated and deployed independently.
