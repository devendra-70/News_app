import feedparser
import logging
from .article_fetcher import fetch_article_content  # Import the article fetcher function
from ..models import RSSLink, NewsArticle  # Assuming RSSLink model exists
from datetime import datetime

logger = logging.getLogger(__name__)

class FeedParser:
    def __init__(self):
        self.date_formats = [
            '%a, %d %b %Y %H:%M:%S %z',
            '%Y-%m-%dT%H:%M:%S%z',
            '%Y-%m-%d %H:%M:%S',
            '%a, %d %b %Y %H:%M:%S GMT',
            '%Y-%m-%dT%H:%M:%SZ'
        ]

    def fetch_all_feeds(self):
        """Fetch all RSS feed URLs from the database."""
        rss_links = RSSLink.objects.all()  # Get all RSSLink entries from the database
        for link in rss_links:
            url = link.url  # Assuming 'url' is the field where the RSS feed link is stored
            logger.info(f"Fetching content from {url}")  # Log for debugging

            # Fetch articles using the fetch_article_content function
            articles = fetch_article_content(url)
            if articles:
                for article_data in articles:
                    if isinstance(article_data, dict):  # Ensure it's a dictionary
                        # Save or update the article in the NewsArticle model
                        article, created = NewsArticle.objects.update_or_create(
                            title=article_data.get('title', ''),
                            defaults={
                                'url': article_data.get('url', ''),
                                'published_at': article_data.get('published_at', ''),
                                'content': article_data.get('content', ''),
                                'source': article_data.get('source', ''),
                                'category': article_data.get('category', 'General')
                            }
                        )
                        if created:
                            logger.info(f"Article '{article_data.get('title')}' added.")
                        else:
                            logger.info(f"Article '{article_data.get('title')}' already exists.")
            else:
                logger.warning(f"No articles fetched from {url}.")

    def fetch_feed(self, feed_url):
        """Fetch and parse a single RSS feed."""
        logger.info(f"Fetching feed: {feed_url}")

        try:
            feed = feedparser.parse(feed_url)

            if feed.entries:
                self._process_feedparser_entries(feed)
            else:
                logger.warning(f"Empty feed: {feed_url}")
        except Exception as e:
            logger.error(f"Error processing feed {feed_url}: {str(e)}")

    def _process_feedparser_entries(self, feed):
        """Process entries parsed by feedparser."""
        for entry in feed.entries:
            try:
                title = entry.title
                link = entry.link
                published = entry.get('published', entry.get('pubDate', ''))

                # Parse the published date with different formats if necessary
                published_at = self._parse_date(published)

                # Fetch article content using the article fetcher
                article_data = fetch_article_content(link)  # Assuming fetch_article_content returns a dict
                if isinstance(article_data, dict):  # Ensure it's a dictionary
                    article_data['published_at'] = published_at
                    article_data['url'] = link  # Ensure the correct URL is added
                    logger.info(f"Saved article: {article_data.get('title')}")
            except Exception as e:
                logger.error(f"Error processing entry: {str(e)}")

    def _parse_date(self, date_str):
        """Try parsing date with different formats."""
        for date_format in self.date_formats:
            try:
                return datetime.strptime(date_str, date_format)
            except ValueError:
                continue
        return None  # Return None if no format matched
