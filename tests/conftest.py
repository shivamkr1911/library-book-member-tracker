import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.store import LibraryStore, create_seeded_store


@pytest.fixture
def store() -> LibraryStore:
    return create_seeded_store()


@pytest.fixture
def client(store: LibraryStore) -> TestClient:
    return TestClient(create_app(store))
