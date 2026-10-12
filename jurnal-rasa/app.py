import sqlite3
from datetime import datetime

from flask import Flask, abort, g, redirect, render_template, request, url_for

app = Flask(__name__)
DATABASE = "diary.db"

# Daftar mood: kunci dipakai di database dan CSS (data-mood)
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
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_error):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    with sqlite3.connect(DATABASE) as db:
        db.execute(
            """CREATE TABLE IF NOT EXISTS entries (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
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
    """Ambil dan validasi data form. Mengembalikan (title, content, mood)."""
    title = request.form.get("title", "").strip()[:100]
    content = request.form.get("content", "").strip()
    mood = request.form.get("mood", "")
    if not content or mood not in MOODS:
        abort(400, "Isi catatan dan mood wajib diisi.")
    return title, content, mood


# ---------- Routes ----------
@app.route("/")
def index():
    db = get_db()
    active_mood = request.args.get("mood")
    if active_mood not in MOODS:
        active_mood = None

    if active_mood:
        entries = db.execute(
            "SELECT * FROM entries WHERE mood = ? ORDER BY created_at DESC", (active_mood,)
        ).fetchall()
    else:
        entries = db.execute("SELECT * FROM entries ORDER BY created_at DESC").fetchall()

    # Statistik mood (jumlah per mood, untuk grafik batang)
    counts = {row["mood"]: row["total"] for row in db.execute(
        "SELECT mood, COUNT(*) AS total FROM entries GROUP BY mood")}
    total = sum(counts.values())
    biggest = max(counts.values(), default=1)

    # Mode ubah: /?ubah=ID
    edit = None
    edit_id = request.args.get("ubah", type=int)
    if edit_id:
        edit = db.execute("SELECT * FROM entries WHERE id = ?", (edit_id,)).fetchone()

    return render_template(
        "index.html", moods=MOODS, entries=entries, counts=counts,
        total=total, biggest=biggest, active_mood=active_mood, edit=edit,
    )


@app.post("/tambah")
def tambah():
    title, content, mood = read_form()
    db = get_db()
    db.execute(
        "INSERT INTO entries (title, content, mood, created_at) VALUES (?, ?, ?, ?)",
        (title, content, mood, datetime.now().isoformat(timespec="minutes")),
    )
    db.commit()
    return redirect(url_for("index"))


@app.post("/ubah/<int:entry_id>")
def ubah(entry_id):
    title, content, mood = read_form()
    db = get_db()
    db.execute(
        "UPDATE entries SET title = ?, content = ?, mood = ? WHERE id = ?",
        (title, content, mood, entry_id),
    )
    db.commit()
    return redirect(url_for("index"))


@app.post("/hapus/<int:entry_id>")
def hapus(entry_id):
    db = get_db()
    db.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
    db.commit()
    return redirect(url_for("index"))


init_db()

if __name__ == "__main__":
    app.run(debug=True)
