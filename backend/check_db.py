"""Show what's actually stored in ai_farming.db (datastore viewer).
Run:  python check_db.py   (from backend/ folder)
"""
import sqlite3
from pathlib import Path

DB = Path(__file__).resolve().parent / "ai_farming.db"

print(f"DB file: {DB}")
print(f"Exists: {DB.exists()} | Size: {DB.stat().st_size if DB.exists() else 0} bytes\n")

if not DB.exists():
    print("No DB file yet. Start backend once: uvicorn main:app --reload")
    raise SystemExit(1)

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row

tables = [r[0] for r in con.execute(
    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
print("Tables:", tables, "\n")

for t in ["plants", "disease_scans", "watering_logs", "health_logs"]:
    if t not in tables:
        print(f"-- {t}: MISSING")
        continue
    count = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    print(f"-- {t}: {count} rows")
    cols = [c[1] for c in con.execute(f"PRAGMA table_info({t})")]
    print(f"   columns: {cols}")
    if count > 0:
        for row in con.execute(f"SELECT * FROM {t} ORDER BY rowid DESC LIMIT 5"):
            print("   ", dict(row))
    print()

con.close()
print("Full detail: open ai_farming.db in 'DB Browser for SQLite',")
print("or API: http://localhost:8000/docs -> GET /api/plants/")
