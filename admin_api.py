# admin_api.py - everything the admin panel can do. Everything in `private` needs a login.
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel
import auth, config
from auth import SESSION_SECONDS, require_admin, sessions
from database import get_db
from scraper import fetch_all

public = APIRouter(prefix="/api/admin")
private = APIRouter(prefix="/api/admin", dependencies=[Depends(require_admin)])


class Login(BaseModel):
    username: str
    password: str

class GoogleLogin(BaseModel):
    credential: str

class SourceUpdate(BaseModel):
    active: bool

class IdList(BaseModel):
    ids: list[int]


def _open_session(response, who):
    token = auth.start_session(who)
    response.set_cookie("admin_session", token, httponly=True, samesite="strict", max_age=SESSION_SECONDS)


# ---------- Login (public) ----------
@public.get("/config")
def login_config():
    return {"google_client_id": config.GOOGLE_CLIENT_ID if config.ADMIN_EMAIL else ""}

@public.post("/login")
def login(data: Login, request: Request, response: Response):
    ip = request.client.host
    if auth.is_locked(ip):
        raise HTTPException(429, "Too many wrong attempts. Try again in 5 minutes.")
    if not auth.check_credentials(data.username, data.password):
        auth.record_fail(ip)
        raise HTTPException(401, "Wrong username or password")
    auth.fails.pop(ip, None)
    _open_session(response, data.username)
    return {"ok": True}

@public.post("/login/google")
def login_google(data: GoogleLogin, request: Request, response: Response):
    ip = request.client.host
    if auth.is_locked(ip):
        raise HTTPException(429, "Too many wrong attempts. Try again in 5 minutes.")
    try:
        who = auth.verify_google(data.credential)
    except HTTPException as e:
        if e.status_code in (401, 403):
            auth.record_fail(ip)
        raise
    auth.fails.pop(ip, None)
    _open_session(response, who)
    return {"ok": True}


# ---------- Private ----------
@private.get("/me")
def me(request: Request):
    return {"who": sessions[request.cookies["admin_session"]][1]}

@private.post("/logout")
def logout(request: Request, response: Response):
    sessions.pop(request.cookies.get("admin_session"), None)
    response.delete_cookie("admin_session")
    return {"ok": True}

@private.get("/stats")
def stats():
    with get_db() as db:
        n = lambda q: db.execute(q).fetchone()[0]
        rows = lambda q: [dict(r) for r in db.execute(q)]
        return {
            "articles": n("SELECT COUNT(*) FROM news_articles"),
            "sources": n("SELECT COUNT(*) FROM news_sources"),
            "active": n("SELECT COUNT(*) FROM news_sources WHERE active=1"),
            "failing": n("SELECT COUNT(*) FROM news_sources WHERE active=1 AND last_status LIKE 'FAILED%'"),
            "last_checked": db.execute("SELECT MAX(last_checked) FROM news_sources").fetchone()[0],
            "by_source": rows("""SELECT s.name, COUNT(a.id) AS count FROM news_sources s
                                 LEFT JOIN news_articles a ON a.source_id = s.id
                                 GROUP BY s.id ORDER BY count DESC"""),
            "by_category": rows("""SELECT c.name, COUNT(a.id) AS count FROM categories c
                                   LEFT JOIN news_articles a ON a.category_id = c.id
                                   GROUP BY c.id ORDER BY count DESC"""),
        }

@private.get("/sources")
def list_sources():
    with get_db() as db:
        return [dict(r) for r in db.execute(
            """SELECT id, name, type, active, last_status, last_checked,
                      (SELECT COUNT(*) FROM news_articles WHERE source_id = news_sources.id) AS articles
               FROM news_sources ORDER BY type, name""")]

@private.put("/sources/{sid}")
def update_source(sid: int, s: SourceUpdate):
    with get_db() as db:
        db.execute("UPDATE news_sources SET active=? WHERE id=?", (int(s.active), sid))
    return {"ok": True}

@private.post("/refresh")
def refresh():
    fetch_all()
    return {"ok": True}

@private.get("/articles")
def list_articles(q: str = "", source: str = "", page: int = 1, size: int = 15):
    size = max(1, min(size, 50))
    where, params = "WHERE 1=1", []
    if q:
        where += " AND a.headline LIKE ?"; params.append(f"%{q[:100]}%")
    if source:
        where += " AND s.name = ?"; params.append(source)
    base = ("FROM news_articles a JOIN news_sources s ON s.id = a.source_id "
            "JOIN categories c ON c.id = a.category_id " + where)
    with get_db() as db:
        total = db.execute("SELECT COUNT(*) " + base, params).fetchone()[0]
        rows = db.execute("SELECT a.id, a.headline, a.link, a.published, s.name AS source, c.name AS category "
                          + base + " ORDER BY a.published DESC LIMIT ? OFFSET ?",
                          params + [size, (max(page, 1) - 1) * size])
        return {"total": total, "items": [dict(r) for r in rows]}

@private.post("/articles/delete")
def delete_articles(data: IdList):
    ids = data.ids[:200]
    if ids:
        with get_db() as db:
            db.execute(f"DELETE FROM news_articles WHERE id IN ({','.join('?' * len(ids))})", ids)
    return {"deleted": len(ids)}