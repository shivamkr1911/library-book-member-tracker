# Library Book & Member Tracker

Internal app for Maple Grove Community Library (fictional). See [docs/requirements.md](docs/requirements.md).

Status: backend (in-memory store + JSON API) and dashboard UI (Jinja2, vanilla JS, CSS) are built.
The dashboard is served at http://127.0.0.1:8000/. The search and filter bar is a marked placeholder.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

## Run

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

API docs: http://127.0.0.1:8000/docs

## Lint and test

```bash
ruff check .
ruff format --check .
pytest
```
