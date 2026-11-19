import html, logging, re, socket, ssl, time
from datetime import datetime, timezone
import certifi
import feedparser
from database import get_db
from sources import SOURCES, CATEGORIES, KEYWORDS

# Fix for Mac: lets Python verify website security certificates
ssl._create_default_https_context = lambda: ssl.create_default_context(cafile=certifi.where())

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("scraper")
socket.setdefaulttimeout(10)   # never wait more than 10s for a slow site

# Makes websites think we are a normal browser, so they do not block us
BROWSER = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120 Safari/537.36"


def seed_sources():
    """Makes the database match sources.py: add/update the listed sources, remove all others."""
    with get_db() as db:
        for c in CATEGORIES:
            db.execute("INSERT OR IGNORE INTO categories(name) VALUES (?)", (c,))
        for name, typ, base, feed in SOURCES:
            db.execute("""INSERT INTO news_sources(name,type,base_url,feed_url) VALUES (?,?,?,?)
                          ON CONFLICT(name) DO UPDATE SET type=excluded.type,
                          base_url=excluded.base_url, feed_url=excluded.feed_url""",
                       (name, typ, base, feed))
        # Remove every source (and its articles) that is NOT listed in sources.py
        names = [row[0] for row in SOURCES]
        marks = ",".join("?" * len(names))
        db.execute(f"DELETE FROM news_articles WHERE source_id IN "
                   f"(SELECT id FROM news_sources WHERE name NOT IN ({marks}))", names)
        db.execute(f"DELETE FROM news_sources WHERE name NOT IN ({marks})", names)


def guess_category(text):
    text = text.lower()
    for cat, words in KEYWORDS.items():
        if any(w in text for w in words):
            return cat
    return "General"


def clean_title(text):
    """Remove HTML code like <a href=...> from a headline."""
    return html.unescape(re.sub(r"<[^>]+>", "", text)).strip()


def find_image(entry):
    for key in ("media_content", "media_thumbnail"):
        if entry.get(key):
            return entry[key][0].get("url")
    for link in entry.get("links", []):
        if link.get("type", "").startswith("image"):
            return link.get("href")
    m = re.search(r'<img[^>]+src="([^"]+)"', entry.get("summary", ""))
    return m.group(1) if m else None


def fetch_all():
    """Runs every 15 minutes: ping each feed, parse, store. Broken feeds are skipped (REQ-2)."""
    db = get_db()
    cats = {r["name"]: r["id"] for r in db.execute("SELECT * FROM categories")}
    for s in db.execute("SELECT * FROM news_sources WHERE active=1").fetchall():
        try:
            feed = feedparser.parse(s["feed_url"], agent=BROWSER)
            if not feed.entries:
                # Explain WHY it failed: what the website really answered
                why = str(feed.get("bozo_exception", "empty feed"))[:120]
                kind = feed.get("headers", {}).get("content-type", "")
                raise ValueError(f"HTTP {feed.get('status', '?')} {kind} - {why}")
            new = 0
            for e in feed.entries[:30]:
                title, link = clean_title(e.get("title", "")), e.get("link")
                if not title or not link:
                    continue
                t = e.get("published_parsed")
                published = (datetime(*t[:6], tzinfo=timezone.utc) if t
                             else datetime.now(timezone.utc)).isoformat()
                cur = db.execute(
                    "INSERT OR IGNORE INTO news_articles(headline,link,image,published,source_id,category_id) "
                    "VALUES (?,?,?,?,?,?)",
                    (title, link, find_image(e), published, s["id"], cats[guess_category(title)]))
                new += cur.rowcount
            status = f"OK (+{new} new)"
        except Exception as ex:                       # skip + log, never crash
            status = f"FAILED: {ex}"
            log.warning("%s -> %s", s["name"], status)
        db.execute("UPDATE news_sources SET last_status=?, last_checked=? WHERE id=?",
                   (status, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), s["id"]))
        db.commit()
        time.sleep(1)                                 # be polite: don't overload their servers
    # Real news arrived, so the "Demo:" sample cards are no longer needed
    db.execute("DELETE FROM news_articles WHERE link LIKE 'https://example.com/demo-%' "
               "AND (SELECT COUNT(*) FROM news_articles WHERE link NOT LIKE 'https://example.com/demo-%') > 0")
    db.commit()
    db.close()
    log.info("Fetch cycle finished")


def seed_demo():
    """A few sample articles so the site is never empty while you test or present."""
    with get_db() as db:
        if db.execute("SELECT COUNT(*) FROM news_articles").fetchone()[0]:
            return
        src = db.execute("SELECT id FROM news_sources LIMIT 1").fetchone()["id"]
        cats = {r["name"]: r["id"] for r in db.execute("SELECT * FROM categories")}
        now = datetime.now(timezone.utc).isoformat()
        for i, (cat, title) in enumerate([
            ("Politics", "Demo: Parliament discusses new digital policy"),
            ("Sports", "Demo: Cricket team prepares for the next tournament"),
            ("Technology", "Demo: Local startups adopt AI tools"),
            ("Entertainment", "Demo: New Bangla film gets festival award"),
            ("Business", "Demo: Export earnings show steady growth"),
            ("General", "Demo: Rain expected across Dhaka this week")]):
            db.execute("INSERT OR IGNORE INTO news_articles(headline,link,published,source_id,category_id) VALUES (?,?,?,?,?)",
                       (title, f"https://example.com/demo-{i}", now, src, cats[cat]))