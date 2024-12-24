import requests
import feedparser
from datetime import datetime
from .models import NewsArticle

NEWS_API_KEY = 'your_newsapi_key_here'

def fetch_news_from_api():
    api_key = '0c2ab5832c004517b889ee0c59156773'  # Ensure the key is in quotes
    url = f'https://newsapi.org/v2/top-headlines?country=us&pageSize=10&apiKey={api_key}'
    response = requests.get(url)
    data = response.json()

    if data.get('status') == 'ok':
        articles = data.get('articles', [])
        for article in articles:
            NewsArticle.objects.update_or_create(
                url=article['url'],  # Use `url` as a unique field to avoid duplicates
                defaults={
                    'title': article['title'],
                    'source': article['source']['name'],
                    'published_at': article['publishedAt'],
                    'summary': article.get('description', ''),
                }
            )


def fetch_news_from_rss():
    rss_url = "https://rss.cnn.com/rss/edition.rss"
    feed = feedparser.parse(rss_url)

    for entry in feed.entries[:10]:
        published_at = datetime(*entry.published_parsed[:6])
        NewsArticle.objects.update_or_create(
            title=entry.title,
            source=feed.feed.title,
            url=entry.link,
            published_at=published_at,
            defaults={
                'summary': entry.summary if hasattr(entry, 'summary') else '',
            }
        )
