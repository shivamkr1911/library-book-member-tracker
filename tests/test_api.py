def test_dashboard(client):
    response = client.get("/api/dashboard")
    assert response.status_code == 200
    assert response.json() == {
        "total_books": 12,
        "available_books": 6,
        "issued_books": 4,
        "active_members": 5,
    }


def test_list_books_includes_borrower(client):
    response = client.get("/api/books")
    assert response.status_code == 200
    books = {b["id"]: b for b in response.json()}
    assert len(books) == 12
    assert books[2]["status"] == "issued"
    assert books[2]["borrower_name"] == "Alice Hartwell"
    assert books[1]["borrower_id"] is None
    assert books[1]["borrower_name"] is None


def test_list_members(client):
    assert len(client.get("/api/members").json()) == 6


def test_list_active_members_excludes_inactive(client):
    response = client.get("/api/members", params={"status": "active"})
    assert response.status_code == 200
    members = response.json()
    assert len(members) == 5
    assert all(m["status"] == "active" for m in members)


def test_list_members_invalid_status(client):
    assert client.get("/api/members", params={"status": "bogus"}).status_code == 422


def test_issue_success(client):
    response = client.post("/api/books/1/issue", json={"member_id": 4})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "issued"
    assert body["borrower_id"] == 4
    assert body["borrower_name"] == "Dmitri Varga"
    assert client.get("/api/dashboard").json()["issued_books"] == 5


def test_issue_unknown_book(client):
    response = client.post("/api/books/999/issue", json={"member_id": 4})
    assert response.status_code == 404
    assert response.json() == {"detail": "Book not found"}


def test_issue_unknown_member(client):
    response = client.post("/api/books/1/issue", json={"member_id": 999})
    assert response.status_code == 404
    assert response.json() == {"detail": "Member not found"}


def test_issue_book_not_available(client):
    before = client.get("/api/dashboard").json()
    for book_id in (2, 6):
        response = client.post(f"/api/books/{book_id}/issue", json={"member_id": 4})
        assert response.status_code == 409
        assert response.json() == {"detail": "Book is not available"}
    assert client.get("/api/dashboard").json() == before


def test_issue_to_inactive_member(client):
    response = client.post("/api/books/1/issue", json={"member_id": 6})
    assert response.status_code == 409
    assert response.json() == {"detail": "Member is not active"}
    book = next(b for b in client.get("/api/books").json() if b["id"] == 1)
    assert book["status"] == "available"


def test_issue_invalid_body(client):
    assert client.post("/api/books/1/issue", json={}).status_code == 422
    assert client.post("/api/books/1/issue", json={"member_id": "abc"}).status_code == 422


def test_return_success(client):
    response = client.post("/api/books/2/return")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "available"
    assert body["borrower_id"] is None
    assert body["borrower_name"] is None


def test_return_unknown_book(client):
    response = client.post("/api/books/999/return")
    assert response.status_code == 404
    assert response.json() == {"detail": "Book not found"}


def test_return_book_not_issued(client):
    for book_id in (1, 6):
        response = client.post(f"/api/books/{book_id}/return")
        assert response.status_code == 409
        assert response.json() == {"detail": "Book is not issued"}


def test_issue_return_round_trip_restores_counts(client):
    before = client.get("/api/dashboard").json()
    assert client.post("/api/books/1/issue", json={"member_id": 4}).status_code == 200
    assert client.post("/api/books/1/return").status_code == 200
    assert client.get("/api/dashboard").json() == before
