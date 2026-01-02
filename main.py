from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime
import sqlite3
import os

app = Flask(__name__)

DB_NAME = "awaroot.db"

def init_db():
    if not os.path.exists(DB_NAME):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                category TEXT NOT NULL,
                value INTEGER,
                note TEXT
            )
        """)
        conn.commit()
        conn.close()

@app.route('/', methods=['GET', 'POST'])
def index():
    init_db()  # sicherstellen, dass DB existiert

    if request.method == 'POST':
        timestamp = datetime.now().isoformat()
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()

        # Drei Hauptwerte + Kommentar speichern
        energie = request.form.get('energie')
        fokus = request.form.get('fokus')
        gefuehl = request.form.get('gefuehl')
        kommentar = request.form.get('kommentar', '')
        gefuehls_text = request.form.get('gefuehls_text', '').strip()

        if energie:
            c.execute("INSERT INTO entries (timestamp, category, value, note) VALUES (?, ?, ?, ?)",
                      (timestamp, 'Energie', int(energie), ''))
        if fokus:
            c.execute("INSERT INTO entries (timestamp, category, value, note) VALUES (?, ?, ?, ?)",
                      (timestamp, 'Fokus', int(fokus), ''))
        if gefuehl:
            c.execute("INSERT INTO entries (timestamp, category, value, note) VALUES (?, ?, ?, ?)",
                      (timestamp, 'Gefühl', int(gefuehl), ''))
        if kommentar:
            c.execute("INSERT INTO entries (timestamp, category, value, note) VALUES (?, ?, ?, ?)",
                      (timestamp, 'Kommentar', None, kommentar))
        if gefuehls_text:
            c.execute("INSERT INTO entries (timestamp, category, value, note) VALUES (?, ?, ?, ?)",
                      (timestamp, 'Gefühlsbeschreibung', None, gefuehls_text))

        conn.commit()
        conn.close()
        return redirect(url_for('index'))

    # Letzte Einträge laden und gruppieren
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        SELECT timestamp, category, value, note 
        FROM entries 
        ORDER BY timestamp DESC
    """)
    all_entries = c.fetchall()
    conn.close()

    # Gruppieren pro Timestamp
    from collections import defaultdict
    grouped = defaultdict(dict)
    for ts, cat, val, note in all_entries:
        short_ts = ts[:16]  # nur Datum+Uhrzeit ohne Sekunden
        if cat == 'Kommentar' or cat == 'Gefühlsbeschreibung':
            grouped[short_ts][cat] = note or ''
        else:
            grouped[short_ts][cat] = val

    # Sortiert nach Zeit (neueste oben), max 20 Gruppen
    recent_groups = sorted(grouped.items(), key=lambda x: x[0], reverse=True)[:20]

    print("Aktuelle Gruppen:", recent_groups)   # nur zum Debuggen / kann auskommentiert werden

    return render_template('index.html', recent_groups=recent_groups)

if __name__ == '__main__':
    app.run(debug=True)