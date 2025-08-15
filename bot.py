import os
import feedparser
import requests
import google.generativeai as genai
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

# =========================
# CONFIG
# =========================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# RSS Feeds for AI News
AI_FEEDS = [
    "https://venturebeat.com/category/ai/feed/",
    "https://www.theverge.com/artificial-intelligence/rss/index.xml",
    "https://techcrunch.com/category/artificial-intelligence/feed/"
]

# Reddit Subreddits
REDDIT_URLS = [
    "https://www.reddit.com/r/MachineLearning/top/.json?t=day&limit=3",
    "https://www.reddit.com/r/Artificial/top/.json?t=day&limit=3"
]

# arXiv AI Research
ARXIV_URL = "http://export.arxiv.org/api/query?search_query=cat:cs.AI+OR+cat:cs.CL&sortBy=submittedDate&sortOrder=descending&max_results=3"

# =========================
# GEMINI SETUP
# =========================
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

def fetch_rss_news():
    news_items = []
    for feed in AI_FEEDS:
        parsed_feed = feedparser.parse(feed)
        for entry in parsed_feed.entries[:2]:
            news_items.append({
                "title": entry.title,
                "link": entry.link
            })
    return news_items

def fetch_reddit_posts():
    posts = []
    headers = {"User-Agent": "Mozilla/5.0"}
    for url in REDDIT_URLS:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            data = res.json()
            for post in data["data"]["children"]:
                posts.append({
                    "title": post["data"]["title"],
                    "link": "https://reddit.com" + post["data"]["permalink"]
                })
    return posts

def fetch_arxiv_papers():
    parsed = feedparser.parse(ARXIV_URL)
    papers = []
    for entry in parsed.entries:
        papers.append({
            "title": entry.title,
            "link": entry.link
        })
    return papers

def fetch_producthunt_tools():
    try:
        res = requests.get("https://www.producthunt.com/feed", timeout=10)  # RSS feed
        parsed = feedparser.parse(res.text)
        tools = []
        for entry in parsed.entries[:3]:
            tools.append({
                "title": entry.title,
                "link": entry.link
            })
        return tools
    except Exception:
        return []

def summarize_with_gemini(news, tools, memes, papers):
    prompt = f"""
    You are an AI Twitter content creator.
    Here is today's AI content with sources:

    NEWS: {news}
    TOOLS: {tools}
    MEMES: {memes}
    PAPERS: {papers}

    Create a short engaging Telegram update with:
    - 2-3 hot AI news item in tweet format + source link
    - 2-3 trending AI tool highlight + source link
    - 2-3 meme/funny caption idea + source link
    - 2-3 research paper insight + source link
    Keep it content slightly longer than a tweet so i can refine it later, add emojis, and make it engaging.
    Make sure to include the source link in the tweet.
    """
    response = model.generate_content(prompt)
    return response.text.strip()

def send_to_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload)

def main():
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    news = fetch_rss_news()
    memes = fetch_reddit_posts()
    papers = fetch_arxiv_papers()
    tools = fetch_producthunt_tools()

    summary = summarize_with_gemini(news, tools, memes, papers)
    telegram_message = f"🧠 AI UPDATE ({now})\n\n{summary}"
    send_to_telegram(telegram_message)

if __name__ == "__main__":
    main()
