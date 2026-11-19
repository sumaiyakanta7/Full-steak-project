import sqlite3

DB_FILE = "news.db"

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row   # lets us use row["name"]
    return conn

def init_db():
    """Create the 3 tables from the ERD: News_Sources, Categories, News_Articles."""
    with get_db() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS news_sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            type TEXT,
            base_url TEXT,
            feed_url TEXT,
            active INTEGER DEFAULT 1,
            last_status TEXT DEFAULT 'not run yet',
            last_checked TEXT
        );
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        );
        CREATE TABLE IF NOT EXISTS news_articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            headline TEXT NOT NULL,
            link TEXT UNIQUE NOT NULL,
            image TEXT,
            published TEXT,
            source_id INTEGER REFERENCES news_sources(id),
            category_id INTEGER REFERENCES categories(id)
        );
        CREATE INDEX IF NOT EXISTS idx_headline  ON news_articles(headline);
        CREATE INDEX IF NOT EXISTS idx_published ON news_articles(published);
        """)

