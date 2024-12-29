import feedparser
import requests
from .models import NewsArticle
from .rss_links import RSS_LINKS
import logging
from datetime import datetime
import xml.etree.ElementTree as ET

# Set up logging
logger = logging.getLogger(__name__)

def fetch_news_from_rss():
    # Ensure only the feeds in RSS_LINKS are processed
    for rss_url in RSS_LINKS:
        try:
            logger.debug(f"Fetching RSS feed: {rss_url}")
            # Fetch and parse using feedparser
            feed = feedparser.parse(rss_url)

            if feed.entries:
                for entry in feed.entries:
                    title = entry.title
                    link = entry.link
                    published = entry.published
                    summary = entry.get('summary', entry.get('description', 'No description available'))

                    # Save or update the article in the database
                    # Convert the published date to a datetime object
                    published_at = datetime.strptime(published, '%a, %d %b %Y %H:%M:%S %z') if published else None

                    # Create or update the article
                    NewsArticle.objects.update_or_create(
                        title=title,
                        source=rss_url,
                        url=link,
                        published_at=published_at,
                        defaults={'summary': summary},
                    )
                    logger.debug(f"Fetched and saved article: {title}")
            else:
                logger.warning(f"No entries found in the feed: {rss_url}")

        except Exception as e:
            logger.error(f"Error parsing feed {rss_url}: {e}")

            # Attempt manual parsing if feedparser fails
            try:
                logger.debug(f"Trying to parse XML feed manually: {rss_url}")
                response = requests.get(rss_url)
                response.raise_for_status()

                # Parse XML content manually
                root = ET.fromstring(response.content)

                # Process the items
                for item in root.findall('.//item'):
                    title = item.find('title').text
                    link = item.find('link').text
                    pub_date = item.find('pubDate').text
                    description = item.find('description').text

                    # Save or update the article
                    published_at = datetime.strptime(pub_date, '%a, %d %b %Y %H:%M:%S %z') if pub_date else None
                    NewsArticle.objects.update_or_create(
                        title=title,
                        source=rss_url,
                        url=link,
                        published_at=published_at,
                        defaults={'summary': description},
                    )
                    logger.debug(f"Fetched and saved article manually: {title}")
            except Exception as e:
                logger.error(f"Error manually parsing feed {rss_url}: {e}")
