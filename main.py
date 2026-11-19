import re, time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles

from admin_api import private, public
from database import get_db, init_db
from scraper import fetch_all, seed_demo, seed_sources

FRONTEND = Path(__file__).resolve().parent.parent / "frontend"


@asynccontextmanager
async def lifespan(app):
    init_db(); seed_sources(); seed_demo()
    scheduler = BackgroundScheduler()
    # Data refresh every 15 minutes; first run starts right now.
    scheduler.add_job(fetch_all, "interval", minutes=15, next_run_time=datetime.now())
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(title="Multi-Source News Aggregator Portal", lifespan=lifespan)

# ---------- Security helpers ----------
hits = defaultdict(deque)

def rate_limit(ip):
    """Max 60 requests per minute per visitor (SRS 5.3)."""
    now, q = time.time(), hits[ip]
    while q and now - q[0] > 60:
        q.popleft()
    if len(q) >= 60:
        raise HTTPException(429, "Too many requests. Please wait a minute.")
    q.append(now)

def clean(text):
    """Remove HTML characters, limit length, escape LIKE wildcards."""
    text = re.sub(r"[<>]", "", text).strip()[:100]
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")

# ---------- Public API ----------
@app.get("/api/news")
def get_news(request: Request, q: str = "", source: str = "", category: str = "", limit: int = 60):
    rate_limit(request.client.host)
    sql = """SELECT a.headline, a.link, a.image, a.published,
                    s.name AS source, s.type AS source_type, c.name AS category
             FROM news_articles a
             JOIN news_sources s ON s.id = a.source_id
             JOIN categories  c ON c.id = a.category_id
             WHERE s.active = 1"""
    params = []
    if q:
        sql += " AND a.headline LIKE ? ESCAPE '\\'"; params.append(f"%{clean(q)}%")
    if source:
        sql += " AND s.name = ?"; params.append(source)
    if category:
        sql += " AND c.name = ?"; params.append(category)
    sql += " ORDER BY a.published DESC LIMIT ?"; params.append(min(limit, 100))   # newest first (REQ-3)
    with get_db() as db:
        return [dict(r) for r in db.execute(sql, params)]   # "?" placeholders block SQL injection

@app.get("/api/sources")
def get_sources():
    with get_db() as db:
        return [dict(r) for r in db.execute("SELECT name, type FROM news_sources WHERE active=1 ORDER BY type, name")]

@app.get("/api/categories")
def get_categories():
    with get_db() as db:
        return [r["name"] for r in db.execute("SELECT name FROM categories")]

# ---------- Admin API (login required, see admin_api.py) ----------
app.include_router(public)
app.include_router(private)

# ---------- Frontend (must be last) ----------
app.mount("/", StaticFiles(directory=FRONTEND, html=True), name="site")