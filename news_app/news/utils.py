import requests
import feedparser
from datetime import datetime
from .models import NewsArticle
from .rss_links import RSS_LINKS

NEWS_API_KEY = 'your_newsapi_key_here'

def fetch_news_from_api(query='', from_date=None, to_date=None):
    # Prepare the URL for the API request
    api_key = '0c2ab5832c004517b889ee0c59156773'
    url = f'https://newsapi.org/v2/everything?q={query}&apiKey={api_key}&pageSize=10'

    # Add date range filter if provided
    if from_date:
        url += f'&from={from_date}'
    if to_date:
        url += f'&to={to_date}'

    response = requests.get(url)
    data = response.json()

    if data.get('status') == 'ok':
        articles = data.get('articles', [])
        for article in articles:
            # Save or update the article in the database
            NewsArticle.objects.update_or_create(
                title=article['title'],
                source=article['source']['name'],
                url=article['url'],
                published_at=article['publishedAt'],
                defaults={
                    'summary': article['description'],
                }
            )


def fetch_news_from_rss():
    for rss_url in RSS_LINKS:
        feed = feedparser.parse(rss_url)

        if 'entries' in feed:
            for entry in feed.entries[:10]:  # Limit to 10 entries per RSS feed
                published_at = datetime(*entry.published_parsed[:6]) if hasattr(entry, 'published_parsed') else None
                NewsArticle.objects.update_or_create(
                    title=entry.title,
                    source=feed.feed.title if hasattr(feed, 'feed') and hasattr(feed.feed, 'title') else 'Unknown',
                    url=entry.link,
                    published_at=published_at,
                    defaults={
                        'summary': entry.summary if hasattr(entry, 'summary') else '',
                    }
                )