from typing import Dict, List, Optional

from app.models import (
    Book,
    BookStatus,
    BookView,
    DashboardSummary,
    Member,
    MemberStatus,
)
from app.seed import seed_books, seed_members


class LibraryError(Exception):
    """Base class for domain errors."""


class BookNotFoundError(LibraryError):
    pass


class MemberNotFoundError(LibraryError):
    pass


class BookNotAvailableError(LibraryError):
    pass


class BookNotIssuedError(LibraryError):
    pass


class MemberNotActiveError(LibraryError):
    pass


class LibraryStore:
    """In-memory store. All business rules live here."""

    def __init__(self, books: List[Book], members: List[Member]) -> None:
        self._books: Dict[int, Book] = {b.id: b for b in books}
        self._members: Dict[int, Member] = {m.id: m for m in members}

    def get_book(self, book_id: int) -> Book:
        try:
            return self._books[book_id]
        except KeyError:
            raise BookNotFoundError(book_id) from None

    def get_member(self, member_id: int) -> Member:
        try:
            return self._members[member_id]
        except KeyError:
            raise MemberNotFoundError(member_id) from None

    def list_members(self, status: Optional[MemberStatus] = None) -> List[Member]:
        return [m for m in self._members.values() if status is None or m.status == status]

    def to_view(self, book: Book) -> BookView:
        borrower = self._members.get(book.borrower_id) if book.borrower_id is not None else None
        return BookView(
            **book.model_dump(),
            borrower_name=borrower.name if borrower else None,
        )

    def list_books(self) -> List[BookView]:
        return [self.to_view(b) for b in self._books.values()]

    def get_book_view(self, book_id: int) -> BookView:
        return self.to_view(self.get_book(book_id))

    def issue_book(self, book_id: int, member_id: int) -> BookView:
        book = self.get_book(book_id)
        member = self.get_member(member_id)
        if book.status != BookStatus.AVAILABLE:
            raise BookNotAvailableError(book_id)
        if member.status != MemberStatus.ACTIVE:
            raise MemberNotActiveError(member_id)
        book.status = BookStatus.ISSUED
        book.borrower_id = member.id
        return self.to_view(book)

    def return_book(self, book_id: int) -> BookView:
        book = self.get_book(book_id)
        if book.status != BookStatus.ISSUED:
            raise BookNotIssuedError(book_id)
        book.status = BookStatus.AVAILABLE
        book.borrower_id = None
        return self.to_view(book)

    def summary(self) -> DashboardSummary:
        books = list(self._books.values())
        return DashboardSummary(
            total_books=len(books),
            available_books=sum(b.status == BookStatus.AVAILABLE for b in books),
            issued_books=sum(b.status == BookStatus.ISSUED for b in books),
            active_members=len(self.list_members(MemberStatus.ACTIVE)),
        )


def create_seeded_store() -> LibraryStore:
    return LibraryStore(seed_books(), seed_members())
