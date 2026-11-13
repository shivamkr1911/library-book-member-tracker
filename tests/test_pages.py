from app.models import BookStatus


def test_index_renders_summary_cards(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    html = response.text
    for label in ("Total Books", "Available Books", "Issued Books", "Active Members"):
        assert label in html
    for key, value in (
        ("total_books", 12),
        ("available_books", 6),
        ("issued_books", 4),
        ("active_members", 5),
    ):
        assert f'data-summary="{key}">{value}<' in html


def test_index_filter_placeholder_is_above_books_table(client):
    html = client.get("/").text
    assert 'id="book-filter-bar"' in html
    assert "FUTURE FEATURE" in html
    assert html.index('id="book-filter-bar"') < html.index('id="books-table"')


def test_index_books_table_columns_and_rows(client):
    html = client.get("/").text
    for column in ("Title", "Author", "Category", "Status", "Current Borrower", "Action"):
        assert f'<th scope="col">{column}</th>' in html
    assert "The Maple Orchard" in html
    assert "Alice Hartwell" in html
    assert 'data-action="issue" data-book-id="1"' in html
    assert 'data-action="return" data-book-id="2"' in html
    # Reserved book 6 has no action button.
    assert 'data-action="issue" data-book-id="6"' not in html
    assert 'data-action="return" data-book-id="6"' not in html


def test_index_status_grid_has_three_columns_with_counts(client):
    html = client.get("/").text
    for status, count in (("available", 6), ("issued", 4), ("reserved", 2)):
        assert f'data-status="{status}"' in html
        assert f'{status.capitalize()} <span class="count">({count})</span>' in html


def test_index_status_grid_empty_column_shows_placeholder(client):
    for book_id in (6, 9):  # the two reserved books
        client.app.state.store.get_book(book_id).status = BookStatus.AVAILABLE
    html = client.get("/").text
    assert 'Reserved <span class="count">(0)</span>' in html
    assert "No books" in html


def test_index_escapes_html(client):
    client.app.state.store.get_book(1).title = "<script>alert(1)</script>"
    html = client.get("/").text
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html


def test_static_assets_served(client):
    assert client.get("/static/css/styles.css").status_code == 200
    assert client.get("/static/js/app.js").status_code == 200
