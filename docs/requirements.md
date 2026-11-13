# Library Book & Member Tracker — Plan

Internal web app for Maple Grove Community Library (fictional). Staff can see library stock at a glance, issue available books to active members, and process returns.

**Stack:** Python + FastAPI, Jinja2 templates, vanilla JS and CSS (no build step), in-memory store seeded with fictional data (no database), pytest, Ruff, GitHub Actions CI.

**Non-goals (this iteration):** persistence, authentication, search/filter (placeholder only), reserving a book from the UI, loan limits, due dates and fines, member management screens.

**Assumptions to confirm:**
1. "Reserved" is a seeded status only. Reserved books cannot be issued and there is no UI to reserve or unreserve them.
2. Only `active` members can borrow. `inactive` members are seeded so the rule can be tested.
3. No per-member loan limit.
4. Data resets on every server restart.

---

## 1. User Stories and Acceptance Criteria

### US-1 Dashboard summary cards
As a librarian, I want summary cards so I can see library status at a glance.
- Four cards show: Total Books, Available Books, Issued Books, Active Members.
- Total = count of all books. Available and Issued = books with that status. Reserved books count only toward Total.
- Active Members = members with status `active`.
- Cards update after an issue or return without a full page reload.

### US-2 Books table
As a librarian, I want a table of all books so I can see who has what.
- Columns: Title, Author, Category, Status, Current Borrower, Action.
- Current Borrower shows the member's name for issued books and an empty marker (e.g. "—") otherwise.
- Status is shown as a labelled badge (text plus colour, not colour alone).
- Rows have an Issue button (available books) or a Return button (issued books). Reserved books have no action button.

### US-3 Issue a book
As a librarian, I want to issue an available book to an active member.
- Clicking Issue opens a control to choose a member. Only active members are listed.
- On confirm, the book becomes `issued` with that member as borrower.
- Table, grid and cards all reflect the change.
- Issuing a book that is not `available` is rejected with a clear message and no state change.
- Issuing to an inactive or unknown member is rejected with a clear message and no state change.

### US-4 Return a book
As a librarian, I want to return an issued book.
- Clicking Return sets the book to `available` and clears the borrower.
- Table, grid and cards all reflect the change.
- Returning a book that is not `issued` is rejected with a clear message and no state change.

### US-5 Book-status grid
As a librarian, I want a grid grouped by status so I can scan stock quickly.
- Three columns: Available, Issued, Reserved. Each has a header with its count.
- Each book appears as a card (title, author) in exactly one column. Issued cards also show the borrower.
- An empty column shows an "No books" placeholder.
- Grid updates after issue and return.

### US-6 Reserved space for search and filter
As a developer, I need a marked placeholder so search and filter can be added later.
- A container directly above the books table is labelled in markup with a comment and `id="book-filter-bar"`.
- It has visible placeholder text, e.g. "Search and filter coming soon".
- It has no behaviour and no backend support yet.

### US-7 Quality gates
As a maintainer, I want automated checks so regressions are caught.
- On push and pull request, GitHub Actions runs `ruff check`, `ruff format --check` and `pytest`.
- The workflow fails if any step fails.

---

## 2. REST Endpoints

Pages are server-rendered. JSON API lives under `/api`. Error responses use FastAPI's standard `{"detail": "..."}` body with generic, non-sensitive messages.

| Method | Path | Purpose | Success | Errors |
|---|---|---|---|---|
| GET | `/` | Render dashboard page (cards, filter placeholder, books table, status grid) from the store | 200 HTML | — |
| GET | `/api/dashboard` | Summary counts: `total_books`, `available_books`, `issued_books`, `active_members` | 200 | — |
| GET | `/api/books` | List all books with `borrower` (id and name, or null) | 200 | — |
| GET | `/api/members` | List members; optional `?status=active` | 200 | 422 invalid status |
| POST | `/api/books/{book_id}/issue` | Body `{"member_id": int}`. Issue an available book to an active member | 200 updated book | 404 unknown book or member; 409 book not available; 409 member not active; 422 invalid body |
| POST | `/api/books/{book_id}/return` | Return an issued book | 200 updated book | 404 unknown book; 409 book not issued |

Notes:
- Initial page render is server-side. After issue or return, vanilla JS calls the API, then re-fetches `/api/dashboard` and `/api/books` and re-renders cards, table and grid.
- Use `409 Conflict` for state-rule violations and `404` for missing resources.
- Dev server binds to `127.0.0.1` only.

---

## 3. Data Model

Pydantic models; in-memory store holds dicts keyed by id.

**Enums**
- `BookStatus`: `available`, `issued`, `reserved`
- `MemberStatus`: `active`, `inactive`

**Book**
| Field | Type | Notes |
|---|---|---|
| `id` | int | unique |
| `title` | str | |
| `author` | str | |
| `category` | str | e.g. Fiction, History, Science, Children |
| `status` | BookStatus | |
| `borrower_id` | int or null | set only when `issued`; must be null otherwise |

**Member**
| Field | Type | Notes |
|---|---|---|
| `id` | int | unique |
| `name` | str | fictional |
| `email` | str | fictional, `example.org` domain |
| `status` | MemberStatus | |

**Other types**
- `IssueRequest`: `member_id: int`
- `BookView`: Book plus `borrower_name` (resolved from the member), used by the table and grid
- `DashboardSummary`: four integer counts

**Store (`LibraryStore`)**
- Holds books and members; seeded from `seed.py`.
- Methods: list books, list members, get book/member, `issue_book(book_id, member_id)`, `return_book(book_id)`, `summary()`.
- Business rules live here and raise domain exceptions that routes map to 404/409. Routes contain no rule logic.
- Seed: about 12 books across at least 4 categories covering all three statuses (issued books have valid borrowers), and about 6 members with at least one inactive. A factory function builds a fresh seeded store so tests are isolated.

**Invariant:** `borrower_id` is non-null if and only if `status == issued`.

---

## 4. Folder Structure

```
library-book-member-tracker/
├── .github/workflows/ci.yml      # Ruff + pytest
├── .gitignore
├── README.md                     # run, test, lint instructions
├── pyproject.toml                # Ruff + pytest config
├── requirements.txt              # runtime deps (pinned)
├── requirements-dev.txt          # pytest, httpx, ruff (pinned)
├── docs/
│   └── requirements.md           # this plan
├── app/
│   ├── __init__.py
│   ├── main.py                   # create_app(), mounts static, includes routers
│   ├── models.py                 # enums and Pydantic models
│   ├── store.py                  # LibraryStore + domain exceptions
│   ├── seed.py                   # fictional books and members
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── pages.py              # GET /
│   │   └── api.py                # /api/*
│   ├── templates/
│   │   ├── base.html
│   │   └── index.html            # cards, filter placeholder, table, grid
│   └── static/
│       ├── css/styles.css
│       └── js/app.js             # fetch, render, issue/return handlers
└── tests/
    ├── conftest.py               # fresh app and TestClient per test
    ├── test_store.py
    ├── test_api.py
    └── test_pages.py
```

---

## 5. Test Strategy

**Tools:** pytest with FastAPI `TestClient`; Ruff for lint and format check. Each test gets a fresh seeded store via a fixture, so there is no shared state.

**Unit tests (`test_store.py`)**
- Seed data covers all statuses, has valid borrowers, and includes an inactive member.
- `issue_book`: success; non-available book; unknown book; unknown member; inactive member.
- `return_book`: success; non-issued book; unknown book.
- Invariant `borrower_id` iff `issued` holds after every operation.
- `summary()` counts match the seed and change correctly after issue and return.

**API tests (`test_api.py`)**
- Each endpoint's success shape and status code.
- 404, 409 and 422 cases from the endpoint table; the state is unchanged after a rejected request.
- Issue then return round trip restores the original counts.
- `/api/members?status=active` excludes inactive members.
- Error bodies contain no stack traces or internals.

**Page tests (`test_pages.py`)**
- `GET /` returns 200 HTML with four summary cards, the `book-filter-bar` placeholder positioned before the books table, the table columns, and three grid columns.
- Seeded book titles and borrower names appear; user-visible text is HTML-escaped (Jinja2 autoescape).

**Frontend:** vanilla JS has no automated tests in this iteration (no build step or JS toolchain). Keep logic thin: fetch, render, and display API error messages. Verify by manual smoke test: issue, return, rejected issue, and card/grid updates.

**CI (`ci.yml`)**
- Triggers: push and pull_request.
- Steps: checkout, set up Python (latest stable supported by dependencies), install from `requirements-dev.txt` with pip caching, `ruff check .`, `ruff format --check .`, `pytest`.
- Minimal `permissions: contents: read`.

---

## 6. Implementation Sub-Tasks

Each is independent and reviewable on its own, done in order.

1. **[ ] Project scaffolding** — `pyproject.toml`, requirements files (latest stable, maintained versions verified at install time), `.gitignore`, README, empty package layout. Outcome: `ruff check` and `pytest` run cleanly on an empty suite.
2. **[ ] Models, seed and store** — enums, Pydantic models, seed data, `LibraryStore` with rules and domain exceptions, plus `test_store.py`. Outcome: store tests pass.
3. **[ ] JSON API** — `create_app()`, `/api` router, exception mapping to 404/409, plus `test_api.py`. Outcome: API tests pass.
4. **[ ] Page, templates and static assets** — `GET /`, `base.html`, `index.html` (cards, filter placeholder, table, grid), CSS, `app.js` for issue/return and re-render, plus `test_pages.py`. Outcome: app works end to end at `http://127.0.0.1:8000`.
5. **[ ] CI** — `.github/workflows/ci.yml` running Ruff and pytest. Outcome: workflow passes on push.

**Security notes applied:** bind to `127.0.0.1`; Jinja2 autoescape on and no `|safe` on user data; server-side validation via Pydantic; generic error messages; pinned dependencies; least-privilege CI token. Authentication is out of scope for this internal prototype; add SSO via OpenID Connect before any deployment beyond localhost.
