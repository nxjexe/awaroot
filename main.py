from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime
import sqlite3
import os
from collections import defaultdict
import plotly.graph_objects as go
import plotly.utils
import json

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
    init_db()

    if request.method == 'POST':
        timestamp = datetime.now().isoformat()
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()

        energie = request.form.get('energie')
        fokus = request.form.get('fokus')
        gefuehl = request.form.get('gefuehl')
        kommentar = request.form.get('kommentar', '').strip()
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

    # Daten laden und gruppieren (wie bisher)
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT timestamp, category, value, note FROM entries ORDER BY timestamp ASC")  # ASC für Charts
    all_entries = c.fetchall()
    conn.close()

    grouped = defaultdict(dict)
    dates = []
    energie_vals = []
    fokus_vals = []
    gefuehl_vals = []

    for ts, cat, val, note in all_entries:
        short_ts = ts[:10]  # nur Datum für Chart (YYYY-MM-DD)
        full_ts = ts[:16]   # für Liste

        if cat in ['Energie', 'Fokus', 'Gefühl']:
            grouped[full_ts][cat] = val
        elif cat == 'Kommentar':
            grouped[full_ts]['Kommentar'] = note or ''
        elif cat == 'Gefühlsbeschreibung':
            grouped[full_ts]['Gefühlsbeschreibung'] = note or ''

        # Für Charts: nur numerische Werte pro Datum sammeln (letzter Wert des Tages)
        if short_ts not in dates:
            dates.append(short_ts)
        if cat == 'Energie':
            energie_vals.append(val)
        elif cat == 'Fokus' and not energie_vals:  # fallback, falls unterschiedliche Anzahl
            energie_vals.append(None)
        # Wir nehmen einfach die letzten Werte pro Tag – simpel, aber effektiv

    # Für Charts: stunden-genaue Daten (letzter Wert pro Stunde)
    hourly = defaultdict(lambda: {'Energie': None, 'Fokus': None, 'Gefühl': None})
    for ts, cat, val, _ in all_entries:
        if cat in ['Energie', 'Fokus', 'Gefühl']:
            hour_ts = ts[:13] + ":00"  # YYYY-MM-DD HH:00
            hourly[hour_ts][cat] = val  # überschreibt mit dem letzten Wert dieser Stunde

    dates = sorted(hourly.keys())
    energie_vals = [hourly[d].get('Energie', None) for d in dates]
    fokus_vals = [hourly[d].get('Fokus', None) for d in dates]
    gefuehl_vals = [hourly[d].get('Gefühl', None) for d in dates]

    # Plotly Chart
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=energie_vals, mode='lines+markers', name='Energie'))
    fig.add_trace(go.Scatter(x=dates, y=fokus_vals, mode='lines+markers', name='Fokus'))
    fig.add_trace(go.Scatter(x=dates, y=gefuehl_vals, mode='lines+markers', name='Gefühl'))
    fig.update_layout(
        title='Dein Trend (stunden-genau)',
        xaxis_title='Zeit',
        yaxis_title='Wert (1–10)',
        yaxis=dict(range=[0, 11]),
        hovermode='x unified'
    )
    chart_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    # Gruppiert für Liste (neueste oben)
    recent_groups = sorted(grouped.items(), key=lambda x: x[0], reverse=True)[:20]

    return render_template('index.html', recent_groups=recent_groups, chart_json=chart_json)

if __name__ == '__main__':
    app.run(debug=True, port=5001)