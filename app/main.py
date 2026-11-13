from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routers import api, pages
from app.store import LibraryStore, create_seeded_store

STATIC_DIR = Path(__file__).resolve().parent / "static"


def create_app(store: LibraryStore = None) -> FastAPI:
    app = FastAPI(title="Library Book & Member Tracker")
    app.state.store = store if store is not None else create_seeded_store()
    app.include_router(pages.router)
    app.include_router(api.router)
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    return app


app = create_app()
