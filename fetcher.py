import requests
import os
from dotenv import load_dotenv

load_dotenv()

NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
NEWSAPI_URL = "https://newsapi.org/v2/everything"

def fetch_articles(user_interests: str, num_articles: int = 5) -> list[dict]:
    params = {
        "q": user_interests,
        "pageSize": num_articles,
        "language": "en",
        "sortBy": "relevancy",
        "apiKey": NEWSAPI_KEY
    }

    response = requests.get(NEWSAPI_URL, params=params)
    response.raise_for_status()

    articles = response.json().get("articles", [])

    return [
        {
            "title": a.get("title", "No title"),
            "description": a.get("description", "No description available"),
            "url": a.get("url", ""),
            "source": a.get("source", {}).get("name", "Unknown")
        }
        for a in articles
    ]

if __name__ == "__main__":
    results = fetch_articles("artificial intelligence, European economics")
    for i, article in enumerate(results, 1):
        print(f"\n--- Article {i} ---")
        print(f"Source: {article['source']}")
        print(f"Title: {article['title']}")
        print(f"Description: {article['description']}")
        print(f"URL: {article['url']}")
