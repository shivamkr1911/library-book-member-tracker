from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.models import BookStatus
from app.routers.api import get_store
from app.store import LibraryStore

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

router = APIRouter()


def parse_status(value: Optional[str]) -> Optional[BookStatus]:
    """The filter form submits an empty string for 'All statuses'."""
    if not value:
        return None
    try:
        return BookStatus(value)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid status") from None


@router.get("/", response_class=HTMLResponse)
def index(
    request: Request,
    q: Optional[str] = Query(default=None, max_length=100),
    category: Optional[str] = Query(default=None, max_length=50),
    status: Optional[str] = Query(default=None, max_length=20),
    store: LibraryStore = Depends(get_store),
) -> HTMLResponse:
    status_filter = parse_status(status)
    all_books = store.list_books()
    filtered_books = store.list_books(q=q, category=category, status=status_filter)
    context = {
        "summary": store.summary(),
        "books": filtered_books,
        "filters": {
            "q": (q or "").strip(),
            "category": category or "",
            "status": status_filter.value if status_filter else "",
        },
        "categories": store.list_categories(),
        "statuses": [s.value for s in BookStatus],
        "columns": [
            (s, [b for b in all_books if b.status == s])
            for s in (BookStatus.AVAILABLE, BookStatus.ISSUED, BookStatus.RESERVED)
        ],
    }
    return templates.TemplateResponse(request, "index.html", context)
