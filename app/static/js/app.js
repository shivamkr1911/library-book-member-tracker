(() => {
  "use strict";

  const STATUSES = ["available", "issued", "reserved"];
  const messageEl = document.getElementById("message");
  const booksBody = document.getElementById("books-body");
  const statusGrid = document.getElementById("status-grid");
  const dialog = document.getElementById("issue-dialog");
  const issueForm = document.getElementById("issue-form");
  const memberSelect = document.getElementById("issue-member");
  const dialogBook = document.getElementById("issue-dialog-book");
  const confirmBtn = document.getElementById("issue-confirm");
  let issuingBookId = null;

  // All dynamic text is set via textContent, never innerHTML.
  function el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function capitalize(word) {
    return word.charAt(0).toUpperCase() + word.slice(1);
  }

  function showMessage(text) {
    messageEl.textContent = text;
    messageEl.hidden = false;
  }

  function clearMessage() {
    messageEl.textContent = "";
    messageEl.hidden = true;
  }

  async function api(path, options) {
    let response;
    try {
      response = await fetch(path, options);
    } catch (err) {
      throw new Error("Could not reach the server. Please try again.");
    }
    let body = null;
    try {
      body = await response.json();
    } catch (err) {
      // Non-JSON body; fall through to generic handling.
    }
    if (!response.ok) {
      const detail = body && typeof body.detail === "string" ? body.detail : null;
      throw new Error(detail || "Request failed. Please try again.");
    }
    return body;
  }

  function postJson(path, payload) {
    const options = { method: "POST" };
    if (payload !== undefined) {
      options.headers = { "Content-Type": "application/json" };
      options.body = JSON.stringify(payload);
    }
    return api(path, options);
  }

  function renderSummary(summary) {
    document.querySelectorAll("[data-summary]").forEach((node) => {
      node.textContent = summary[node.dataset.summary];
    });
  }

  function renderTable(books) {
    booksBody.replaceChildren();
    if (books.length === 0) {
      const row = el("tr", "empty-row");
      row.id = "books-empty";
      const cell = el("td", "", "No books match your search or filters.");
      cell.colSpan = 6;
      row.append(cell);
      booksBody.append(row);
      return;
    }
    books.forEach((book) => {
      const row = el("tr");
      row.dataset.bookId = book.id;
      row.append(
        el("td", "", book.title),
        el("td", "", book.author),
        el("td", "", book.category),
      );

      const statusCell = el("td");
      statusCell.append(el("span", `badge badge-${book.status}`, capitalize(book.status)));
      row.append(statusCell, el("td", "", book.borrower_name || "—"));

      const actionCell = el("td");
      if (book.status === "available" || book.status === "issued") {
        const isIssue = book.status === "available";
        const btn = el("button", isIssue ? "btn" : "btn btn-secondary", isIssue ? "Issue" : "Return");
        btn.type = "button";
        btn.dataset.action = isIssue ? "issue" : "return";
        btn.dataset.bookId = book.id;
        btn.dataset.bookTitle = book.title;
        actionCell.append(btn);
      }
      row.append(actionCell);
      booksBody.append(row);
    });
  }

  function renderGrid(books) {
    statusGrid.replaceChildren();
    STATUSES.forEach((status) => {
      const items = books.filter((b) => b.status === status);
      const column = el("div", "grid-column");
      column.dataset.status = status;

      const heading = el("h3", "", `${capitalize(status)} `);
      heading.append(el("span", "count", `(${items.length})`));
      column.append(heading);

      const list = el("div", "grid-items");
      if (items.length === 0) {
        list.append(el("p", "empty", "No books"));
      }
      items.forEach((book) => {
        const card = el("div", "book-card");
        card.append(el("strong", "", book.title), el("span", "", book.author));
        if (book.borrower_name) {
          card.append(el("span", "borrower", `Borrower: ${book.borrower_name}`));
        }
        list.append(card);
      });
      column.append(list);
      statusGrid.append(column);
    });
  }

  // The applied filters live in the page URL (the filter form is a plain GET form).
  // Only non-empty, known parameters are forwarded to the API.
  function currentFilterQuery() {
    const current = new URLSearchParams(window.location.search);
    const query = new URLSearchParams();
    ["q", "category", "status"].forEach((key) => {
      const value = (current.get(key) || "").trim();
      if (value) query.set(key, value);
    });
    const text = query.toString();
    return text ? `?${text}` : "";
  }

  async function refresh() {
    // The table honours the applied filters; the summary cards and status grid
    // always describe the whole library.
    const [summary, allBooks, tableBooks] = await Promise.all([
      api("/api/dashboard"),
      api("/api/books"),
      api(`/api/books${currentFilterQuery()}`),
    ]);
    renderSummary(summary);
    renderTable(tableBooks);
    renderGrid(allBooks);
  }

  async function refreshQuietly() {
    try {
      await refresh();
    } catch (err) {
      showMessage(err.message);
    }
  }

  async function openIssueDialog(bookId, title) {
    clearMessage();
    let members;
    try {
      members = await api("/api/members?status=active");
    } catch (err) {
      showMessage(err.message);
      return;
    }
    memberSelect.replaceChildren();
    members.forEach((m) => {
      const option = el("option", "", m.name);
      option.value = m.id;
      memberSelect.append(option);
    });
    issuingBookId = bookId;
    dialogBook.textContent = title;
    dialog.showModal();
  }

  async function returnBook(bookId) {
    clearMessage();
    try {
      await postJson(`/api/books/${encodeURIComponent(bookId)}/return`);
    } catch (err) {
      showMessage(err.message);
    }
    await refreshQuietly();
  }

  booksBody.addEventListener("click", (event) => {
    const btn = event.target.closest("button[data-action]");
    if (!btn) return;
    if (btn.dataset.action === "issue") {
      openIssueDialog(btn.dataset.bookId, btn.dataset.bookTitle);
    } else if (btn.dataset.action === "return") {
      returnBook(btn.dataset.bookId);
    }
  });

  document.getElementById("issue-cancel").addEventListener("click", () => dialog.close());

  issueForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const memberId = Number.parseInt(memberSelect.value, 10);
    if (Number.isNaN(memberId)) return;
    confirmBtn.disabled = true;
    try {
      await postJson(`/api/books/${encodeURIComponent(issuingBookId)}/issue`, {
        member_id: memberId,
      });
    } catch (err) {
      showMessage(err.message);
    } finally {
      confirmBtn.disabled = false;
      dialog.close();
    }
    await refreshQuietly();
  });
})();
