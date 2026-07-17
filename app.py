import os
import re
import sqlite3
import secrets
import string

from datetime import datetime
from flask import Flask, g, jsonify, redirect, render_template, request, url_for


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "link_shortener.db")

app = Flask(__name__, template_folder="templates")

# Base62 alphabet for short codes
ALPHABET = string.ascii_letters + string.digits


def get_db():
    if "db" not in g:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        g.db = conn
    return g.db


@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS links (
                code TEXT PRIMARY KEY,
                original_url TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_links_original ON links(original_url)"
        )
        conn.commit()
    finally:
        conn.close()


def is_valid_url(url: str) -> bool:
    # Basic validation: requires http(s)
    return re.match(r"^https?://", url, flags=re.IGNORECASE) is not None


def generate_code(length: int = 7) -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(length))


def create_short_link(original_url: str) -> str:
    db = get_db()

    # Reuse existing mapping if URL already exists
    row = db.execute(
        "SELECT code FROM links WHERE original_url = ? LIMIT 1",
        (original_url,),
    ).fetchone()
    if row:
        return row["code"]

    # Otherwise, create a new one (retry on rare collisions)
    for _ in range(10):
        code = generate_code()
        try:
            db.execute(
                "INSERT INTO links(code, original_url, created_at) VALUES (?, ?, ?)",
                (code, original_url, datetime.utcnow().isoformat()),
            )
            db.commit()
            return code
        except sqlite3.IntegrityError:
            continue

    raise RuntimeError("Could not generate unique short code")


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/api/shorten", methods=["POST"])
def api_shorten():
    data = request.get_json(silent=True) or {}
    original_url = data.get("url", "").strip()

    if not original_url:
        return jsonify({"error": "Missing 'url'"}), 400
    if not is_valid_url(original_url):
        return jsonify({"error": "URL must start with http:// or https://"}), 400

    code = create_short_link(original_url)
    short_url = url_for("redirect_to_original", code=code, _external=True)
    return jsonify({"code": code, "short_url": short_url})


@app.route("/<code>", methods=["GET"])
def redirect_to_original(code: str):
    db = get_db()
    row = db.execute("SELECT original_url FROM links WHERE code = ?", (code,)).fetchone()
    if not row:
        return render_template("404.html"), 404

    return redirect(row["original_url"], code=302)


if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", "5000"))
    # Host 0.0.0.0 helps if you want access from other devices on the network
    app.run(host="0.0.0.0", port=port, debug=True)

