import os
import sqlite3
from datetime import datetime, timedelta, timezone

from flask import Flask, abort, g, redirect, render_template, request, url_for

# Folder "public" dibaca Vercel untuk file statis (CSS/JS).
app = Flask(__name__, static_folder="public", static_url_path="")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Ada DATABASE_URL -> Postgres (permanen, untuk Vercel). Tidak ada -> SQLite (komputer sendiri).
POSTGRES_URL = os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL")
ON_VERCEL = bool(os.environ.get("VERCEL"))
SQLITE_PATH = "/tmp/diary.db" if ON_VERCEL else os.path.join(BASE_DIR, "diary.db")

WIB = timezone(timedelta(hours=7))  # server Vercel memakai UTC

MOODS = {
    "senang": {"label": "Senang", "emoji": "😄"},
    "tenang": {"label": "Tenang", "emoji": "😌"},
    "biasa": {"label": "Biasa saja", "emoji": "😐"},
    "cemas": {"label": "Cemas", "emoji": "😰"},
    "sedih": {"label": "Sedih", "emoji": "😢"},
    "marah": {"label": "Marah", "emoji": "😠"},
}

HARI = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
BULAN = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli",
         "Agustus", "September", "Oktober", "November", "Desember"]


# ---------- Database ----------
def get_db():
    if "db" not in g:
        if POSTGRES_URL:
            import psycopg
            from psycopg.rows import dict_row
            g.db = psycopg.connect(POSTGRES_URL, row_factory=dict_row)
        else:
            g.db = sqlite3.connect(SQLITE_PATH)
            g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_error):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def sql(query):
    """Kode memakai tanda ?, Postgres memakai %s."""
    return query.replace("?", "%s") if POSTGRES_URL else query


def fetch_all(query, params=()):
    return get_db().execute(sql(query), params).fetchall()


def fetch_one(query, params=()):
    return get_db().execute(sql(query), params).fetchone()


def run(query, params=()):
    db = get_db()
    db.execute(sql(query), params)
    db.commit()


def init_db():
    pk = "SERIAL PRIMARY KEY" if POSTGRES_URL else "INTEGER PRIMARY KEY AUTOINCREMENT"
    with app.app_context():
        run(
            f"""CREATE TABLE IF NOT EXISTS entries (
                    id {pk},
                    title TEXT,
                    content TEXT NOT NULL,
                    mood TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )"""
        )


@app.template_filter("tanggal")
def format_tanggal(value):
    d = datetime.fromisoformat(value)
    return f"{HARI[d.weekday()]}, {d.day} {BULAN[d.month - 1]} {d.year}, pukul {d:%H.%M}"


def read_form():
    title = request.form.get("title", "").strip()[:100]
    content = request.form.get("content", "").strip()
    mood = request.form.get("mood", "")
    if not content or mood not in MOODS:
        abort(400, "Isi catatan dan mood wajib diisi.")
    return title, content, mood


# ---------- Routes ----------
@app.route("/")
def index():
    active_mood = request.args.get("mood")
    if active_mood not in MOODS:
        active_mood = None

    if active_mood:
        entries = fetch_all(
            "SELECT * FROM entries WHERE mood = ? ORDER BY created_at DESC", (active_mood,)
        )
    else:
        entries = fetch_all("SELECT * FROM entries ORDER BY created_at DESC")

    counts = {row["mood"]: row["total"] for row in fetch_all(
        "SELECT mood, COUNT(*) AS total FROM entries GROUP BY mood")}
    total = sum(counts.values())
    biggest = max(counts.values(), default=1)

    edit = None
    edit_id = request.args.get("ubah", type=int)
    if edit_id:
        edit = fetch_one("SELECT * FROM entries WHERE id = ?", (edit_id,))

    return render_template(
        "index.html", moods=MOODS, entries=entries, counts=counts,
        total=total, biggest=biggest, active_mood=active_mood, edit=edit,
    )


@app.post("/tambah")
def tambah():
    title, content, mood = read_form()
    now = datetime.now(WIB).replace(tzinfo=None).isoformat(timespec="minutes")
    run(
        "INSERT INTO entries (title, content, mood, created_at) VALUES (?, ?, ?, ?)",
        (title, content, mood, now),
    )
    return redirect(url_for("index"))


@app.post("/ubah/<int:entry_id>")
def ubah(entry_id):
    title, content, mood = read_form()
    run(
        "UPDATE entries SET title = ?, content = ?, mood = ? WHERE id = ?",
        (title, content, mood, entry_id),
    )
    return redirect(url_for("index"))


@app.post("/hapus/<int:entry_id>")
def hapus(entry_id):
    run("DELETE FROM entries WHERE id = ?", (entry_id,))
    return redirect(url_for("index"))


init_db()

if __name__ == "__main__":
    app.run(debug=True)