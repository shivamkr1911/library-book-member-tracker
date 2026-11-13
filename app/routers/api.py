from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request

from app.models import BookView, DashboardSummary, IssueRequest, Member, MemberStatus
from app.store import (
    BookNotAvailableError,
    BookNotFoundError,
    BookNotIssuedError,
    LibraryStore,
    MemberNotActiveError,
    MemberNotFoundError,
)

router = APIRouter(prefix="/api")


def get_store(request: Request) -> LibraryStore:
    return request.app.state.store


@router.get("/dashboard", response_model=DashboardSummary)
def dashboard(store: LibraryStore = Depends(get_store)) -> DashboardSummary:
    return store.summary()


@router.get("/books", response_model=List[BookView])
def list_books(store: LibraryStore = Depends(get_store)) -> List[BookView]:
    return store.list_books()


@router.get("/members", response_model=List[Member])
def list_members(
    status: Optional[MemberStatus] = None, store: LibraryStore = Depends(get_store)
) -> List[Member]:
    return store.list_members(status)


@router.post("/books/{book_id}/issue", response_model=BookView)
def issue_book(
    book_id: int, body: IssueRequest, store: LibraryStore = Depends(get_store)
) -> BookView:
    try:
        return store.issue_book(book_id, body.member_id)
    except BookNotFoundError:
        raise HTTPException(status_code=404, detail="Book not found") from None
    except MemberNotFoundError:
        raise HTTPException(status_code=404, detail="Member not found") from None
    except BookNotAvailableError:
        raise HTTPException(status_code=409, detail="Book is not available") from None
    except MemberNotActiveError:
        raise HTTPException(status_code=409, detail="Member is not active") from None


@router.post("/books/{book_id}/return", response_model=BookView)
def return_book(book_id: int, store: LibraryStore = Depends(get_store)) -> BookView:
    try:
        return store.return_book(book_id)
    except BookNotFoundError:
        raise HTTPException(status_code=404, detail="Book not found") from None
    except BookNotIssuedError:
        raise HTTPException(status_code=409, detail="Book is not issued") from None
