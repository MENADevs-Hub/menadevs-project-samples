"""
Application-level security regression tests for the hardened portal.
"""

import pytest

from app import app

XSS_PAYLOAD = '<img src=x onerror=alert(1)>'


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client


def test_search_escapes_user_input(client):
    response = client.get("/search", query_string={"q": XSS_PAYLOAD})
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "<img" not in body
    assert "&lt;img" in body


def test_dashboard_escapes_username(client):
    client.post("/login", data={"username": XSS_PAYLOAD}, follow_redirects=True)
    response = client.get("/dashboard")
    body = response.get_data(as_text=True)
    assert "<img" not in body
    assert "&lt;img" in body


def test_settings_escapes_display_name(client):
    client.post("/login", data={"username": XSS_PAYLOAD}, follow_redirects=True)
    response = client.get("/settings")
    body = response.get_data(as_text=True)
    assert "<img" not in body
    assert "&lt;img" in body


def test_index_escapes_session_username(client):
    client.post("/login", data={"username": XSS_PAYLOAD}, follow_redirects=True)
    response = client.get("/")
    body = response.get_data(as_text=True)
    assert "<img" not in body


def test_redirect_rejects_external_targets(client):
    for target in (
        "https://evil.example/phish",
        "//evil.example/phish",
        "javascript:alert(1)",
    ):
        response = client.get("/redirect", query_string={"next": target})
        assert response.status_code == 400, target


def test_redirect_allows_internal_and_trusted_hosts(client):
    response = client.get(
        "/redirect",
        query_string={"next": "/dashboard"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers["Location"] == "/dashboard"

    response = client.get(
        "/redirect",
        query_string={"next": "https://example.com/welcome"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers["Location"] == "https://example.com/welcome"


def test_session_cookie_flags(client):
    assert app.config["SESSION_COOKIE_HTTPONLY"] is True
    assert app.config["SESSION_COOKIE_SAMESITE"] in ("Lax", "Strict", "lax", "strict")
    response = client.post("/login", data={"username": "tester"}, follow_redirects=False)
    cookie = response.headers.get("Set-Cookie", "").lower()
    assert "httponly" in cookie
    assert "samesite" in cookie


def test_security_headers_on_home(client):
    response = client.get("/")
    csp = response.headers.get("Content-Security-Policy", "")
    assert csp and "*" not in csp
    assert "'unsafe-inline'" not in csp.split("script-src", 1)[-1]
    assert "'unsafe-eval'" not in csp
    assert response.headers.get("X-Frame-Options")
    assert response.headers.get("X-Content-Type-Options")
    assert response.headers.get("Referrer-Policy")
    assert response.headers.get("Permissions-Policy")


def test_legitimate_search_still_renders_query(client):
    response = client.get("/search", query_string={"q": "quarterly"})
    assert response.status_code == 200
    assert "quarterly" in response.get_data(as_text=True)


def test_announcements_list(client):
    response = client.get("/announcements")
    assert response.status_code == 200
    assert "Q3 Planning" in response.get_data(as_text=True)


def test_login_logout_flow(client):
    client.post("/login", data={"username": "testuser"}, follow_redirects=True)
    dash = client.get("/dashboard")
    assert "testuser" in dash.get_data(as_text=True)
    client.get("/logout", follow_redirects=True)
    dash = client.get("/dashboard")
    assert "guest" in dash.get_data(as_text=True)
