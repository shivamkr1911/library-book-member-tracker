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


# --- Search and filtering (issue #1) ---


def titles(books):
    return {b.title for b in books}


def test_list_books_without_filters_returns_all(store):
    assert len(store.list_books()) == 12


def test_search_matches_title_case_insensitively(store):
    assert titles(store.list_books(q="maple")) == {"The Maple Orchard"}
    assert titles(store.list_books(q="MAPLE ORCHARD")) == {"The Maple Orchard"}


def test_search_matches_author(store):
    assert titles(store.list_books(q="greta foss")) == {
        "Pip and the Paper Boat",
        "The Lantern Fox",
    }


def test_search_matches_partial_text_in_title_or_author(store):
    # "ell" is in the author "Rowan Ellis" only; "ter" is in several titles.
    assert titles(store.list_books(q="ell")) == {"The Maple Orchard"}
    assert len(store.list_books(q="ter")) >= 2


def test_search_ignores_surrounding_whitespace_and_blank_means_all(store):
    assert titles(store.list_books(q="  maple  ")) == {"The Maple Orchard"}
    assert len(store.list_books(q="   ")) == 12


def test_search_with_no_match_returns_empty(store):
    assert store.list_books(q="zzz-no-such-book") == []


def test_filter_by_category(store):
    books = store.list_books(category="Science")
    assert len(books) == 3
    assert {b.category for b in books} == {"Science"}


def test_filter_by_category_is_case_insensitive(store):
    assert len(store.list_books(category="science")) == 3


def test_filter_by_unknown_category_returns_empty(store):
    assert store.list_books(category="Poetry") == []


@pytest.mark.parametrize(
    ("status", "expected"),
    [(BookStatus.AVAILABLE, 6), (BookStatus.ISSUED, 4), (BookStatus.RESERVED, 2)],
)
def test_filter_by_status(store, status, expected):
    books = store.list_books(status=status)
    assert len(books) == expected
    assert {b.status for b in books} == {status}


def test_combined_search_category_and_status(store):
    assert titles(store.list_books(q="greta", category="Children", status=BookStatus.RESERVED)) == {
        "The Lantern Fox"
    }
    assert titles(store.list_books(category="Science", status=BookStatus.AVAILABLE)) == {
        "Understanding Tides"
    }
    assert titles(store.list_books(q="maya", status=BookStatus.AVAILABLE)) == {
        "Sourdough Seasons",
        "One-Pot Winters",
    }


def test_combined_filters_with_no_overlap_return_empty(store):
    assert store.list_books(q="maple", category="Science") == []
    assert store.list_books(q="greta", status=BookStatus.ISSUED) == []


def test_filtered_results_still_include_borrower_names(store):
    (book,) = store.list_books(q="birchwood")
    assert book.status == BookStatus.ISSUED
    assert book.borrower_name == "Alice Hartwell"


def test_filter_reflects_status_change_after_issue_and_return(store):
    assert titles(store.list_books(q="maple", status=BookStatus.AVAILABLE)) == {"The Maple Orchard"}
    store.issue_book(1, 4)
    assert store.list_books(q="maple", status=BookStatus.AVAILABLE) == []
    assert titles(store.list_books(q="maple", status=BookStatus.ISSUED)) == {"The Maple Orchard"}
    store.return_book(1)
    assert titles(store.list_books(q="maple", status=BookStatus.AVAILABLE)) == {"The Maple Orchard"}


def test_list_categories_is_sorted_and_unique(store):
    assert store.list_categories() == [
        "Children",
        "Cooking",
        "Fiction",
        "History",
        "Nature",
        "Science",
    ]
