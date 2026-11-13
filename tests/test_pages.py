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


def test_index_filter_bar_is_above_books_table(client):
    html = client.get("/").text
    assert 'id="book-filter-bar"' in html
    assert 'id="filter-form"' in html
    assert "coming soon" not in html
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


# --- Search and filtering (issue #1) ---


def table_html(html):
    return html.split('id="books-body"')[1].split("</tbody>")[0]


def test_filter_bar_has_search_category_status_and_clear_controls(client):
    html = client.get("/").text
    assert 'name="q"' in html
    assert 'name="category"' in html
    assert 'name="status"' in html
    assert '<option value="">All categories</option>' in html
    assert '<option value="">All statuses</option>' in html
    for category in ("Children", "Cooking", "Fiction", "History", "Nature", "Science"):
        assert f'<option value="{category}">{category}</option>' in html
    for status in ("available", "issued", "reserved"):
        assert f'<option value="{status}">{status.capitalize()}</option>' in html
    assert 'id="clear-filters"' in html
    assert 'href="/"' in html


def test_index_search_filters_table_rows(client):
    rows = table_html(client.get("/", params={"q": "maple"}).text)
    assert "The Maple Orchard" in rows
    assert "Letters from Birchwood" not in rows


def test_index_search_by_author(client):
    rows = table_html(client.get("/", params={"q": "ines duarte"}).text)
    assert "Rivers of the Old Province" in rows
    assert "The Maple Orchard" not in rows


def test_index_category_filter(client):
    rows = table_html(client.get("/", params={"category": "Cooking"}).text)
    assert "Sourdough Seasons" in rows
    assert "One-Pot Winters" in rows
    assert "The Maple Orchard" not in rows


def test_index_status_filter(client):
    rows = table_html(client.get("/", params={"status": "reserved"}).text)
    assert "The Quiet Atom" in rows
    assert "The Lantern Fox" in rows
    assert "The Maple Orchard" not in rows


def test_index_combined_filters(client):
    rows = table_html(
        client.get("/", params={"q": "greta", "category": "Children", "status": "available"}).text
    )
    assert "Pip and the Paper Boat" in rows
    assert "The Lantern Fox" not in rows


def test_index_keeps_issue_and_return_buttons_in_filtered_rows(client):
    rows = table_html(client.get("/", params={"category": "Fiction"}).text)
    assert 'data-action="issue" data-book-id="1"' in rows
    assert 'data-action="return" data-book-id="2"' in rows


def test_index_empty_state_when_nothing_matches(client):
    html = client.get("/", params={"q": "zzz-no-such-book"}).text
    assert 'id="books-empty"' in table_html(html)
    assert "No books match your search or filters." in html
    assert 'data-action="issue"' not in table_html(html)


def test_index_no_empty_state_when_results_exist(client):
    assert 'id="books-empty"' not in client.get("/").text


def test_index_filters_are_reflected_in_controls(client):
    html = client.get("/", params={"q": "maple", "category": "Fiction", "status": "available"}).text
    assert 'value="maple"' in html
    assert '<option value="Fiction" selected>Fiction</option>' in html
    assert '<option value="available" selected>Available</option>' in html


def test_index_clear_filters_shows_all_books(client):
    filtered = client.get("/", params={"q": "maple"}).text
    assert table_html(filtered).count("<tr data-book-id=") == 1
    cleared = client.get("/").text  # the Clear filters link goes to "/"
    assert table_html(cleared).count("<tr data-book-id=") == 12
    empty_form = client.get("/", params={"q": "", "category": "", "status": ""}).text
    assert table_html(empty_form).count("<tr data-book-id=") == 12


def test_index_filters_do_not_change_cards_or_status_grid(client):
    html = client.get("/", params={"q": "zzz-no-such-book"}).text
    assert 'data-summary="total_books">12<' in html
    assert 'Available <span class="count">(6)</span>' in html
    assert 'Issued <span class="count">(4)</span>' in html
    assert 'Reserved <span class="count">(2)</span>' in html


def test_index_invalid_status_filter_is_rejected(client):
    assert client.get("/", params={"status": "bogus"}).status_code == 422


def test_index_escapes_search_text_in_input(client):
    html = client.get("/", params={"q": '"><script>alert(1)</script>'}).text
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html


def test_javascript_forwards_filters_and_handles_empty_state(client):
    js = client.get("/static/js/app.js").text
    assert "currentFilterQuery" in js
    assert "No books match your search or filters." in js
