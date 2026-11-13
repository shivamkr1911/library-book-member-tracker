import pytest

from app.models import BookStatus, MemberStatus
from app.store import (
    BookNotAvailableError,
    BookNotFoundError,
    BookNotIssuedError,
    MemberNotActiveError,
    MemberNotFoundError,
)

# Seed facts: book 1 available, 2 issued (member 1), 6 reserved; member 6 inactive.


def assert_invariant(store):
    for book in store.list_books():
        assert (book.borrower_id is not None) == (book.status == BookStatus.ISSUED)


def test_seed_covers_all_statuses_and_valid_borrowers(store):
    books = store.list_books()
    assert {b.status for b in books} == set(BookStatus)
    assert len({b.category for b in books}) >= 4
    for book in books:
        if book.status == BookStatus.ISSUED:
            assert book.borrower_name is not None
    assert any(m.status == MemberStatus.INACTIVE for m in store.list_members())
    assert_invariant(store)


def test_summary_matches_seed(store):
    summary = store.summary()
    books = store.list_books()
    assert summary.total_books == len(books)
    assert summary.available_books == sum(b.status == BookStatus.AVAILABLE for b in books)
    assert summary.issued_books == sum(b.status == BookStatus.ISSUED for b in books)
    assert summary.active_members == len(store.list_members(MemberStatus.ACTIVE))


def test_issue_book_success(store):
    before = store.summary()
    view = store.issue_book(1, 4)
    assert view.status == BookStatus.ISSUED
    assert view.borrower_id == 4
    assert view.borrower_name == store.get_member(4).name
    after = store.summary()
    assert after.available_books == before.available_books - 1
    assert after.issued_books == before.issued_books + 1
    assert after.total_books == before.total_books
    assert_invariant(store)


@pytest.mark.parametrize("book_id", [2, 6])
def test_issue_non_available_book_rejected(store, book_id):
    snapshot = store.get_book(book_id).model_copy()
    with pytest.raises(BookNotAvailableError):
        store.issue_book(book_id, 4)
    assert store.get_book(book_id) == snapshot


def test_issue_unknown_book_rejected(store):
    with pytest.raises(BookNotFoundError):
        store.issue_book(999, 4)


def test_issue_unknown_member_rejected(store):
    with pytest.raises(MemberNotFoundError):
        store.issue_book(1, 999)
    assert store.get_book(1).status == BookStatus.AVAILABLE


def test_issue_to_inactive_member_rejected(store):
    with pytest.raises(MemberNotActiveError):
        store.issue_book(1, 6)
    assert store.get_book(1).status == BookStatus.AVAILABLE
    assert store.get_book(1).borrower_id is None


def test_return_book_success(store):
    view = store.return_book(2)
    assert view.status == BookStatus.AVAILABLE
    assert view.borrower_id is None
    assert view.borrower_name is None
    assert_invariant(store)


@pytest.mark.parametrize("book_id", [1, 6])
def test_return_non_issued_book_rejected(store, book_id):
    snapshot = store.get_book(book_id).model_copy()
    with pytest.raises(BookNotIssuedError):
        store.return_book(book_id)
    assert store.get_book(book_id) == snapshot


def test_return_unknown_book_rejected(store):
    with pytest.raises(BookNotFoundError):
        store.return_book(999)


def test_issue_then_return_restores_summary(store):
    before = store.summary()
    store.issue_book(1, 4)
    store.return_book(1)
    assert store.summary() == before
