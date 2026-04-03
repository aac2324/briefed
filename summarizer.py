import os
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version="2024-12-01-preview"
)

DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")

def summarize_articles(articles: list[dict], user_interests: str) -> str:
    article_text = ""
    for i, article in enumerate(articles, 1):
        article_text += f"""
Article {i}:
Source: {article['source']}
Title: {article['title']}
Description: {article['description']}
URL: {article['url']}
"""

    prompt = f"""
You are a personalized news assistant. The user is interested in: {user_interests}.

Below are today's news articles. For each one:
- Write a 2-3 sentence summary in clear, intelligent language
- Focus on what matters to this specific user
- Skip or briefly dismiss articles that are clearly irrelevant or low quality
- End each summary with the source and URL

Format your response like this for each article:

📰 [Article Title]
[Your 2-3 sentence summary]
🔗 [Source] — [URL]

---

Articles:
{article_text}
"""

    response = client.chat.completions.create(
        model=DEPLOYMENT,
        messages=[
            {"role": "system", "content": "You are a concise, intelligent news summarizer."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.4,
        max_completion_tokens=1000
    )

    return response.choices[0].message.content


if __name__ == "__main__":
    from fetcher import fetch_articles

    interests = "artificial intelligence, European economics"
    articles = fetch_articles(interests)
    summary = summarize_articles(articles, interests)
    print(summary)
