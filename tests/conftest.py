import pytest
from fastapi.testclient import TestClient

from api.main import app

@pytest.fixture(scope="session")
def client():
    """
    Shared TestClient for all test.
    """

    return TestClient(app)