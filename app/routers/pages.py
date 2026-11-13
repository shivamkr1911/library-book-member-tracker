from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.models import BookStatus
from app.routers.api import get_store
from app.store import LibraryStore

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def index(request: Request, store: LibraryStore = Depends(get_store)) -> HTMLResponse:
    books = store.list_books()
    context = {
        "summary": store.summary(),
        "books": books,
        "columns": [
            (status, [b for b in books if b.status == status])
            for status in (BookStatus.AVAILABLE, BookStatus.ISSUED, BookStatus.RESERVED)
        ],
    }
    return templates.TemplateResponse(request, "index.html", context)
