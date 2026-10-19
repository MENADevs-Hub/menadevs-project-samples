"""
Application security regression tests.

Extend this file as part of your security audit.
"""

import pytest

from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client


def test_app_serves_homepage(client):
    """Smoke test — the application starts and serves the index page."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"Internal Portal" in response.data
