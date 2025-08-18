# 


import os
import feedparser
import requests
import google.generativeai as genai
from datetime import datetime

# =========================
# CONFIG
# =========================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# === NEWS RSS ===
AI_FEEDS = [
    "https://venturebeat.com/category/ai/feed/",
    "https://www.theverge.com/ai-artificial-intelligence",
    "https://techcrunch.com/category/artificial-intelligence/feed/",
    "https://ai.googleblog.com/feeds/posts/default",
    "https://blog.research.google/feeds"
    "https://openai.com/news/",
    "https://research.facebook.com/blog/rss/",
    "https://www.technologyreview.com/feed/",
]

# === REDDIT ===
REDDIT_SUBREDDITS = [
    ("r/MachineLearning", 3),
    ("r/Artificial", 3),
    ("r/MLMemes", 2),
    ("r/ComputationalLinguistics", 2),
]

# === ARXIV ===
ARXIV_CATEGORIES = ["cs.AI", "cs.CL", "cs.CV", "cs.LG", "stat.ML"]

# === PRODUCT HUNT ===
PRODUCT_HUNT_RSS = "https://www.producthunt.com/feed"

# === GITHUB ===
GITHUB_TOPICS = ["machine-learning", "transformers", "llm"]

# === HACKER NEWS ===
HN_AI_SEARCH = "https://hnrss.org/newest?q=AI"

# === PAPERS WITH CODE ===
PWC_FEED = "https://paperswithcode.com/feeds/recent-releases"

# === YOUTUBE (optional) ===
YOUTUBE_CHANNELS = [
    # add rss urls like: "https://www.youtube.com/feeds/videos.xml?channel_id=XYZ"
]

# =========================
# GEMINI SETUP
# =========================
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")


# =========================
# FETCHERS
# =========================
def fetch_rss(feeds, limit=2):
    items = []
    for feed in feeds:
        parsed = feedparser.parse(feed)
        for entry in parsed.entries[:limit]:
            items.append({"title": entry.title, "link": entry.link})
    return items


def fetch_reddit(subs):
    posts = []
    headers = {"User-Agent": "Mozilla/5.0"}
    for sub, limit in subs:
        url = f"https://www.reddit.com/{sub}/top/.json?t=day&limit={limit}"
        try:
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                data = res.json()
                for post in data["data"]["children"]:
                    posts.append({
                        "title": post["data"]["title"],
                        "link": "https://reddit.com" + post["data"]["permalink"]
                    })
        except Exception:
            continue
    return posts


def fetch_arxiv(categories, max_results=3):
    query = "+OR+".join([f"cat:{c}" for c in categories])
    url = f"http://export.arxiv.org/api/query?search_query={query}&sortBy=submittedDate&sortOrder=descending&max_results={max_results}"
    parsed = feedparser.parse(url)
    return [{"title": e.title, "link": e.link} for e in parsed.entries]


def fetch_producthunt(limit=3):
    try:
        parsed = feedparser.parse(PRODUCT_HUNT_RSS)
        return [{"title": e.title, "link": e.link} for e in parsed.entries[:limit]]
    except Exception:
        return []


def fetch_hn(limit=5):
    parsed = feedparser.parse(HN_AI_SEARCH)
    return [{"title": e.title, "link": e.link} for e in parsed.entries[:limit]]


def fetch_pwc(limit=3):
    parsed = feedparser.parse(PWC_FEED)
    return [{"title": e.title, "link": e.link} for e in parsed.entries[:limit]]


def fetch_github(topics, per_topic=2):
    repos = []
    headers = {"Accept": "application/vnd.github.v3+json"}
    for topic in topics:
        url = f"https://api.github.com/search/repositories?q=topic:{topic}&sort=stars&order=desc&per_page={per_topic}"
        try:
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                data = r.json().get("items", [])
                for repo in data:
                    repos.append({"title": repo["full_name"], "link": repo["html_url"]})
        except Exception:
            continue
    return repos


# =========================
# SUMMARIZER
# =========================
def summarize_with_gemini(news, tools, memes, papers, hn, github, pwc):
    prompt = f"""
    You are an AI Twitter/Telegram content creator.
    Here is today's fresh AI content with sources:

    NEWS: {news}
    TOOLS: {tools}
    REDDIT/MEMES: {memes}
    PAPERS (arXiv): {papers}
    HACKERNEWS: {hn}
    GITHUB: {github}
    PWC: {pwc}

    Create a concise engaging Telegram update with:
    - 2-3 🔥 AI news items (tweet-style, with source link)
    - 2-3 🚀 trending AI tools/products (with source link)
    - 2-3 🤖 memes/funny AI bits (short, with link)
    - 2-3 📑 research paper highlights (with link)
    - 1-2 📌 Hacker News or GitHub insights (with link)
    Use emojis, keep it natural and engaging, and include links inline.
    """
    response = model.generate_content(prompt)
    return response.text.strip()


def send_to_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    requests.post(url, json=payload)


# =========================
# MAIN
# =========================
def main():
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    news = fetch_rss(AI_FEEDS)
    memes = fetch_reddit(REDDIT_SUBREDDITS)
    papers = fetch_arxiv(ARXIV_CATEGORIES)
    tools = fetch_producthunt()
    hn = fetch_hn()
    github = fetch_github(GITHUB_TOPICS)
    pwc = fetch_pwc()

    summary = summarize_with_gemini(news, tools, memes, papers, hn, github, pwc)
    telegram_message = f"🧠 AI UPDATE ({now})\n\n{summary}"
    send_to_telegram(telegram_message)


if __name__ == "__main__":
    main()
