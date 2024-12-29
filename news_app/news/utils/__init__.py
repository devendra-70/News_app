# news/utils/__init__.py
from .feed_parser import FeedParser

def fetch_news_from_rss():
    parser = FeedParser()
    parser.fetch_all_feeds()