# news/utils/feed_parser.py
import feedparser
import xml.etree.ElementTree as ET
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from dateutil import parser as date_parser
from ..models import NewsArticle
import logging
from ..rss_links import RSS_LINKS

logger = logging.getLogger(__name__)

class FeedParser:
    def __init__(self):
        self.parsers = {
            'RSS': self._parse_rss,
            'XML': self._parse_xml,
            'ATOM': self._parse_atom,
            'JSON': self._parse_json
        }
        self.date_formats = [
            '%a, %d %b %Y %H:%M:%S %z',  # RFC 822 format
            '%Y-%m-%dT%H:%M:%S%z',       # ISO 8601
            '%Y-%m-%d %H:%M:%S',         # Basic datetime
            '%a, %d %b %Y %H:%M:%S GMT', # Alternative RFC 822
            '%Y-%m-%dT%H:%M:%SZ'         # UTC format
        ]

    def fetch_all_feeds(self):
        """Fetch all feeds from RSS_LINKS"""
        for rss_url in RSS_LINKS:
            try:
                self.fetch_feed(rss_url)
            except Exception as e:
                logger.error(f"Error fetching feed {rss_url}: {str(e)}")

    def fetch_feed(self, feed_url):
        """Fetch and parse a single feed"""
        logger.debug(f"Fetching feed: {feed_url}")
        
        try:
            # Try feedparser first
            feed = feedparser.parse(feed_url)
            
            if feed.entries:
                self._process_feedparser_entries(feed, feed_url)
            else:
                # If feedparser fails to find entries, try manual parsing
                self._try_manual_parsing(feed_url)
                
        except Exception as e:
            logger.error(f"Error processing feed {feed_url}: {str(e)}")
            # Try manual parsing as fallback
            self._try_manual_parsing(feed_url)

    def _process_feedparser_entries(self, feed, feed_url):
        """Process entries parsed by feedparser"""
        for entry in feed.entries:
            try:
                title = entry.title
                link = entry.link
                published = entry.get('published', entry.get('pubDate', entry.get('updated', '')))
                summary = entry.get('summary', entry.get('description', 'No description available'))

                # Parse the published date
                published_at = self._parse_date(published)

                # Save or update the article
                NewsArticle.objects.update_or_create(
                    title=title,
                    source=feed_url,
                    url=link,
                    defaults={
                        'summary': summary,
                        'published_at': published_at,
                        'category': 'General'  # Default category
                    }
                )
                logger.debug(f"Saved article: {title}")
            except Exception as e:
                logger.error(f"Error processing entry from {feed_url}: {str(e)}")

    def _parse_xml(self, content, feed_url):
        """Parse XML feed content"""
        articles = []
        try:
            root = ET.fromstring(content)
            for item in root.findall('.//item'):
                article = {
                    'title': self._get_xml_text(item, 'title'),
                    'url': self._get_xml_text(item, 'link'),
                    'summary': self._get_xml_text(item, 'description'),
                    'published_at': self._parse_date(self._get_xml_text(item, 'pubDate')),
                    'source': feed_url,
                    'category': self._get_xml_text(item, 'category') or 'General'
                }
                articles.append(article)
        except Exception as e:
            logger.error(f"Error parsing XML content: {str(e)}")
        return articles

    def _parse_atom(self, content, feed_url):
        """Parse Atom feed content"""
        articles = []
        try:
            root = ET.fromstring(content)
            for entry in root.findall('.//{http://www.w3.org/2005/Atom}entry'):
                article = {
                    'title': self._get_xml_text(entry, './/{http://www.w3.org/2005/Atom}title'),
                    'url': self._get_xml_link(entry),
                    'summary': self._get_xml_text(entry, './/{http://www.w3.org/2005/Atom}summary'),
                    'published_at': self._parse_date(self._get_xml_text(entry, './/{http://www.w3.org/2005/Atom}published')),
                    'source': feed_url,
                    'category': 'General'
                }
                articles.append(article)
        except Exception as e:
            logger.error(f"Error parsing Atom content: {str(e)}")
        return articles

    def _parse_rss(self, content, feed_url):
        """Parse RSS feed content"""
        articles = []
        try:
            root = ET.fromstring(content)
            for item in root.findall('.//item'):
                article = {
                    'title': self._get_xml_text(item, 'title'),
                    'url': self._get_xml_text(item, 'link'),
                    'summary': self._get_xml_text(item, 'description'),
                    'published_at': self._parse_date(self._get_xml_text(item, 'pubDate')),
                    'source': feed_url,
                    'category': self._get_xml_text(item, 'category') or 'General'
                }
                articles.append(article)
        except Exception as e:
            logger.error(f"Error parsing RSS content: {str(e)}")
        return articles

    def _parse_json(self, content, feed_url):
        """Parse JSON feed content"""
        articles = []
        try:
            import json
            data = json.loads(content)
            items = data.get('items', []) or data.get('entries', [])
            
            for item in items:
                article = {
                    'title': item.get('title', ''),
                    'url': item.get('url', item.get('link', '')),
                    'summary': item.get('summary', item.get('description', '')),
                    'published_at': self._parse_date(item.get('published', item.get('date', ''))),
                    'source': feed_url,
                    'category': item.get('category', 'General')
                }
                articles.append(article)
        except Exception as e:
            logger.error(f"Error parsing JSON content: {str(e)}")
        return articles

    def _try_manual_parsing(self, feed_url):
        """Attempt manual parsing of the feed"""
        try:
            logger.debug(f"Attempting manual parsing: {feed_url}")
            response = requests.get(feed_url, timeout=10)
            response.raise_for_status()
            content = response.content

            # Try to determine feed type and parse accordingly
            feed_type = self._determine_feed_type(content)
            parser = self.parsers.get(feed_type)
            
            if parser:
                articles = parser(content, feed_url)
                self._save_articles(articles)
            else:
                logger.error(f"Unsupported feed type for {feed_url}")

        except Exception as e:
            logger.error(f"Error in manual parsing of {feed_url}: {str(e)}")

    def _determine_feed_type(self, content):
        """Determine the type of feed from its content"""
        try:
            root = ET.fromstring(content)
            
            # Check for RSS
            if root.tag == 'rss' or 'rss' in root.tag:
                return 'RSS'
            
            # Check for Atom
            if 'atom' in root.tag or '{http://www.w3.org/2005/Atom}feed' in root.tag:
                return 'ATOM'
            
            # Generic XML
            return 'XML'
        
        except ET.ParseError:
            # Try parsing as JSON
            try:
                import json
                json.loads(content)
                return 'JSON'
            except:
                return None

    def _parse_date(self, date_str):
        """Parse date string to datetime object"""
        if not date_str:
            return datetime.now()

        # Try multiple date formats
        for date_format in self.date_formats:
            try:
                return datetime.strptime(date_str, date_format)
            except ValueError:
                continue

        # If standard formats fail, try dateutil parser
        try:
            return date_parser.parse(date_str)
        except:
            return datetime.now()

    def _get_xml_text(self, element, tag):
        """Safely get text from XML element"""
        try:
            found = element.find(tag)
            return found.text.strip() if found is not None and found.text else ''
        except:
            return ''

    def _get_xml_link(self, entry):
        """Get link from Atom entry"""
        try:
            link = entry.find('.//{http://www.w3.org/2005/Atom}link')
            return link.get('href', '') if link is not None else ''
        except:
            return ''

    def _save_articles(self, articles):
        """Save parsed articles to database"""
        for article_data in articles:
            try:
                NewsArticle.objects.update_or_create(
                    title=article_data['title'],
                    source=article_data['source'],
                    url=article_data['url'],
                    defaults={
                        'summary': article_data['summary'],
                        'published_at': article_data['published_at'],
                        'category': article_data.get('category', 'General')
                    }
                )
            except Exception as e:
                logger.error(f"Error saving article {article_data.get('url', 'Unknown URL')}: {str(e)}")