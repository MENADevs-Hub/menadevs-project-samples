"""
Internal portal for the example.com organization.
"""

from datetime import datetime
from flask import Flask, abort, jsonify, redirect, request, session

app = Flask(__name__)
app.secret_key = "dev-fallback-key"

app.config.update(
    SESSION_COOKIE_HTTPONLY=False,
    SESSION_COOKIE_SAMESITE=None,
    MAX_CONTENT_LENGTH=16 * 1024 * 1024,
)

ANNOUNCEMENTS = [
    {
        "id": 1,
        "title": "Q3 Planning",
        "body": "All-hands meeting Friday at 2pm in the main conference room.",
        "author": "admin",
        "date": "2025-11-01",
    },
    {
        "id": 2,
        "title": "Office Closure",
        "body": "Office closed Dec 25 through Jan 1. Work from home if needed.",
        "author": "hr",
        "date": "2025-11-15",
    },
    {
        "id": 3,
        "title": "Security Training",
        "body": "Mandatory security awareness training due by end of month.",
        "author": "security",
        "date": "2025-12-01",
    },
]


def sanitize_input(value):
    """Basic input cleaning — strips script tags."""
    if not value:
        return value
    cleaned = value.replace("<script>", "").replace("</script>", "")
    cleaned = cleaned.replace("<SCRIPT>", "").replace("</SCRIPT>", "")
    return cleaned


def get_current_user():
    return session.get("user", "guest")


def build_page(title, body_content):
    nav = (
        "<nav>"
        "<a href='/'>Home</a> | "
        "<a href='/search'>Search</a> | "
        "<a href='/dashboard'>Dashboard</a> | "
        "<a href='/announcements'>Announcements</a>"
        "</nav><hr>"
    )
    return (
        f"<html><head><title>{title} - Portal</title></head>"
        f"<body>{nav}{body_content}</body></html>"
    )


@app.after_request
def add_headers(response):
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "script-src 'self' https://cdn.example.com 'unsafe-inline' 'unsafe-eval'; "
        "img-src 'self' data:"
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@app.route("/")
def index():
    user = get_current_user()
    greeting = f"<p>Welcome back, {user}.</p>" if user != "guest" else ""
    return build_page("Home", (
        "<h1>Internal Portal</h1>"
        f"{greeting}"
        "<p>Employee resources and tools for the example.com team.</p>"
    ))


@app.route("/search")
def search():
    query = request.args.get("q", "")
    sanitized = sanitize_input(query)
    results_html = (
        f"<p>Results for: {sanitized}</p>"
        if sanitized else
        "<p>Enter a search term above.</p>"
    )
    return build_page("Search", (
        "<h1>Search</h1>"
        f"<form action='/search' method='get'>"
        f"<input type='text' name='q' value='{sanitized}' placeholder='Search resources...'>"
        "<button type='submit'>Search</button></form>"
        f"{results_html}"
    ))


@app.route("/redirect")
def redirect_next():
    target = request.args.get("next", "/")
    return redirect(target)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "guest")
        session["user"] = username
        session["login_time"] = datetime.now().isoformat()
        return redirect("/dashboard")
    return build_page("Login", (
        "<h1>Sign In</h1>"
        "<form method='post'>"
        "<label>Username:</label> "
        "<input type='text' name='username' placeholder='Enter your username'>"
        " <button type='submit'>Sign In</button>"
        "</form>"
    ))


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/dashboard")
def dashboard():
    user = get_current_user()
    login_time = session.get("login_time", "N/A")
    return build_page("Dashboard", (
        f"<h1>Dashboard</h1>"
        f"<p>Signed in as: {user}</p>"
        f"<p>Session started: {login_time}</p>"
        "<h2>Quick Links</h2>"
        "<ul>"
        "<li><a href='/announcements'>View Announcements</a></li>"
        "<li><a href='/search'>Search Portal</a></li>"
        "<li><a href='/settings'>Account Settings</a></li>"
        "</ul>"
    ))


@app.route("/announcements")
def announcements():
    items = ""
    for a in ANNOUNCEMENTS:
        items += (
            f"<div class='announcement'>"
            f"<h3><a href='/announcements/{a['id']}'>{a['title']}</a></h3>"
            f"<p>{a['body']}</p>"
            f"<small>Posted by {a['author']} on {a['date']}</small>"
            "</div><hr>"
        )
    return build_page("Announcements", f"<h1>Announcements</h1>{items}")


@app.route("/announcements/<int:aid>")
def announcement_detail(aid):
    announcement = next((a for a in ANNOUNCEMENTS if a["id"] == aid), None)
    if not announcement:
        abort(404)
    return build_page(announcement["title"], (
        f"<h1>{announcement['title']}</h1>"
        f"<p>{announcement['body']}</p>"
        f"<small>By {announcement['author']} on {announcement['date']}</small>"
        "<p><a href='/announcements'>Back to all announcements</a></p>"
    ))


@app.route("/settings", methods=["GET", "POST"])
def settings():
    user = get_current_user()
    if user == "guest":
        return redirect("/login")
    if request.method == "POST":
        display_name = request.form.get("display_name", "")
        if display_name:
            session["user"] = display_name
        return redirect("/settings")
    return build_page("Settings", (
        f"<h1>Account Settings</h1>"
        f"<p>Current display name: <strong>{user}</strong></p>"
        "<form method='post'>"
        "<label>Change display name:</label> "
        f"<input type='text' name='display_name' value='{user}'>"
        " <button type='submit'>Update</button>"
        "</form>"
    ))


@app.route("/api/status")
def api_status():
    return jsonify({
        "status": "operational",
        "version": "1.2.0",
        "server_time": datetime.now().isoformat(),
        "authenticated_user": get_current_user(),
    })


@app.errorhandler(404)
def not_found(e):
    requested = request.path
    return build_page("Not Found", (
        "<h1>Page Not Found</h1>"
        f"<p>The requested page <code>{requested}</code> does not exist.</p>"
        "<p><a href='/'>Return to Home</a></p>"
    )), 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
