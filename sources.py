# The 7 news sources the portal tracks.
# If a source shows FAILED in the Admin panel, find that site's RSS link and replace it here.
# The 7 news sources the portal tracks.
# If a source shows FAILED in the Admin panel, find that site's RSS link and replace it here.
SOURCES = [
    # (name, type, website, rss_feed_link)
    ("Prothom Alo",           "Newspaper",  "https://en.prothomalo.com",   "https://en.prothomalo.com/feed/"),
    ("Kaler Kantho",          "Newspaper",  "https://www.kalerkantho.com", "https://news.google.com/rss/search?q=site:kalerkantho.com+when:7d&hl=bn&gl=BD&ceid=BD:bn"),
    ("The Business Standard", "Newspaper",  "https://www.tbsnews.net",     "https://www.tbsnews.net/rss.xml"),
    ("Somoy News",            "TV Channel", "https://www.somoynews.com.bd",    "https://news.google.com/rss/search?q=site:somoynews.com.bd+when:7d&hl=bn&gl=BD&ceid=BD:bn"),
    ("Jamuna TV",             "TV Channel", "https://jamuna.tv",           "https://news.google.com/rss/search?q=site:jamuna.tv+when:7d&hl=bn&gl=BD&ceid=BD:bn"),
    ("Channel 24",            "TV Channel", "https://www.channel24bd.tv",  "https://news.google.com/rss/search?q=site:channel24bd.tv+when:7d&hl=bn&gl=BD&ceid=BD:bn"),
    ("DBC News",              "TV Channel", "https://dbcnews.tv",          "https://news.google.com/rss/search?q=site:dbcnews.tv+when:7d&hl=bn&gl=BD&ceid=BD:bn"),
    ("NTV",                   "TV Channel", "https://www.ntvbd.com",       "https://news.google.com/rss/search?q=site:ntvbd.com+when:7d&hl=bn&gl=BD&ceid=BD:bn"),
]

CATEGORIES = ["Politics", "Sports", "Technology", "Entertainment", "Business", "General"]

# Simple keyword rules to decide a news item's category.
KEYWORDS = {
    "Politics":      ["election", "minister", "parliament", "government", "party", "বিএনপি", "আওয়ামী", "সংসদ", "নির্বাচন"],
    "Sports":        ["cricket", "football", "match", "tournament", "bpl", "ক্রিকেট", "ফুটবল", "খেলা"],
    "Technology":    ["tech", "ai ", "software", "mobile", "internet", "app ", "প্রযুক্তি"],
    "Entertainment": ["film", "movie", "actor", "drama", "music", "সিনেমা", "নাটক", "বিনোদন"],
    "Business":      ["bank", "market", "economy", "taka", "export", "stock", "ব্যাংক", "অর্থনীতি", "বাজার"],
}
