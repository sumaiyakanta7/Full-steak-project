# auth.py - who may enter the admin panel (only you).
# Two ways in: Google sign-in with YOUR Gmail, or your own username + password.
import hashlib, hmac, json, secrets, time
from pathlib import Path
from fastapi import HTTPException, Request
import config

AUTH_FILE = Path(__file__).resolve().parent / "admin.json"   # username + HASHED password
SESSION_SECONDS = 2 * 60 * 60                                # stay logged in for 2 hours
sessions = {}    # login token -> (expiry time, who)
fails = {}       # visitor ip -> (failed attempts, locked until)


def _hash(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 200_000).hex()

def save_credentials(username, password):
    salt = secrets.token_hex(16)
    AUTH_FILE.write_text(json.dumps({"username": username, "salt": salt, "hash": _hash(password, salt)}))

def check_credentials(username, password):
    if not AUTH_FILE.exists():
        return False
    d = json.loads(AUTH_FILE.read_text())
    ok_user = hmac.compare_digest(username.encode(), d["username"].encode())
    ok_pass = hmac.compare_digest(_hash(password, d["salt"]).encode(), d["hash"].encode())
    return ok_user and ok_pass

def verify_google(credential):
    """Ask Google if the login token is real, then check it is YOUR Gmail. Returns your name."""
    if not config.GOOGLE_CLIENT_ID or not config.ADMIN_EMAIL:
        raise HTTPException(400, "Google login is not set up in config.py")
    from google.oauth2 import id_token
    from google.auth.transport import requests as g_requests
    try:
        info = id_token.verify_oauth2_token(credential, g_requests.Request(), config.GOOGLE_CLIENT_ID)
    except Exception:
        raise HTTPException(401, "Google login failed")
    if not info.get("email_verified") or info.get("email", "").lower() != config.ADMIN_EMAIL.lower():
        raise HTTPException(403, "This Google account is not allowed")
    return info.get("name") or info["email"]

def is_locked(ip):
    return time.time() < fails.get(ip, (0, 0))[1]

def record_fail(ip):
    n = fails.get(ip, (0, 0))[0] + 1
    fails[ip] = (n, time.time() + 300 if n >= 5 else 0)   # 5 wrong tries = locked for 5 minutes

def start_session(who):
    token = secrets.token_urlsafe(32)
    sessions[token] = (time.time() + SESSION_SECONDS, who)
    return token

def require_admin(request: Request):
    """Every private admin route runs this first. No valid login = 401."""
    if sessions.get(request.cookies.get("admin_session"), (0, ""))[0] < time.time():
        raise HTTPException(401, "Please log in")