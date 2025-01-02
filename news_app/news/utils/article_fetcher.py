import requests
from bs4 import BeautifulSoup
import logging
from datetime import datetime
from urllib.parse import urlparse
import xml.etree.ElementTree as ET
from typing import Optional, List, Dict, Union

logger = logging.getLogger(__name__)

def fetch_article_content(url: str) -> Optional[Union[List[Dict], Dict]]:
    """
    Enhanced article content fetcher that handles both RSS feeds and regular articles.
    Supports multiple fallback methods for content extraction.

    Args:
        url: The URL to fetch content from

    Returns:
        Optional[Union[List[Dict], Dict]]: Article data or None if fetching fails
        For RSS feeds, returns a list of article dictionaries
        For single articles, returns a dictionary with article data
    """
    print(f"Fetching articles from: {url}")
    try:
        # Configure headers to mimic a browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }

        # Make the request
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        # Check if it's an XML (RSS) feed
        if "xml" in response.headers.get("Content-Type", "") or url.endswith(".rss"):
            return _process_rss_feed(response.content, url)
        else:
            return _process_html_article(response, url)

    except requests.RequestException as e:
        logger.error(f"Request failed for {url}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error processing {url}: {str(e)}", exc_info=True)
        return None

def _process_rss_feed(content: bytes, url: str) -> Optional[List[Dict]]:
    """Process RSS feed content and return a list of articles with full content."""
    try:
        root = ET.fromstring(content)
        articles = []
        
        # Configure headers once for all requests
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }

        for item in root.findall(".//item"):
            try:
                title = item.find("title").text
                link = item.find("link").text
                published_date = item.find("pubDate").text

                # Always fetch the full article content from the URL
                article_response = requests.get(link, headers=headers, timeout=15)
                if article_response.ok:
                    article_data = _process_html_article(article_response, link)
                    if article_data:
                        # Preserve the RSS publication date as it's often more reliable
                        article_data['published_at'] = datetime.strptime(
                            published_date, 
                            "%a, %d %b %Y %H:%M:%S %z"
                        )
                        articles.append(article_data)
                    else:
                        logger.warning(f"Failed to extract content from {link}")
                else:
                    logger.warning(f"Failed to fetch article from {link}: {article_response.status_code}")

            except requests.RequestException as e:
                logger.error(f"Request failed for article {link}: {str(e)}")
                continue
            except Exception as e:
                logger.error(f"Error processing RSS item: {str(e)}")
                continue

        return articles if articles else None
        
    except Exception as e:
        logger.error(f"Error processing RSS feed: {str(e)}")
        return None

def _process_html_article(response: requests.Response, url: str) -> Optional[Dict]:
    """Process HTML article content and return article data."""
    soup = BeautifulSoup(response.content, 'html.parser', from_encoding=response.encoding)
    _clean_html(soup)

    content = _extract_content(soup)
    if not content:
        logger.warning(f"Could not extract content for URL: {url}")
        return None

    return {
        'title': _extract_title(soup),
        'content': content,
        'source': _extract_source(soup, url),
        'published_at': _extract_date(soup),
        'url': url
    }

def _clean_html(soup: BeautifulSoup) -> None:
    """Remove unwanted elements from the HTML content."""
    # Remove hidden elements
    for hidden in soup.find_all(style=lambda value: value and 'display:none' in value.lower()):
        hidden.decompose()

    # Remove unwanted tags
    unwanted_tags = [
        'script', 'style', 'iframe', 'img', 'button', 'input', 'nav',
        'footer', 'header', 'aside', 'form', 'noscript', 'figure',
        'meta', 'link', 'svg', 'path'
    ]
    for tag in unwanted_tags:
        for element in soup.find_all(tag):
            element.decompose()

    # Convert links to text
    for a in soup.find_all('a'):
        a.replaceWith(a.text.strip())

def _extract_content(soup: BeautifulSoup) -> Optional[str]:
    """Extract content using multiple fallback methods."""
    content_identifiers = [
        {'tag': 'article'},
        {'tag': 'div', 'class_': 'article-content'},
        {'tag': 'div', 'class_': 'post-content'},
        {'tag': 'div', 'class_': 'entry-content'},
        {'tag': 'div', 'id': 'content'},
        {'tag': 'div', 'class_': 'content'},
        {'tag': 'div', 'class_': 'story-content'},
        {'tag': 'div', 'class_': 'main-content'},
        {'tag': 'div', 'role': 'main'},
        {'tag': 'main'},
    ]

    # Try each container type
    content = None
    for identifier in content_identifiers:
        found = soup.find(**identifier)
        if found and len(found.text.strip()) > 100:
            content = found
            break

    # Fallback: Look for the largest div with substantial text
    if not content:
        divs = soup.find_all('div')
        content = max(divs, key=lambda d: len(d.text.strip()), default=None)

    # If still no content, use body
    if not content:
        content = soup.find('body')

    if not content:
        return None

    # Extract and format the content
    formatted_content = ""
    
    # Process headings
    seen_headings = set()
    for heading in content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        text = heading.text.strip()
        if text and text not in seen_headings and len(text) < 200:
            seen_headings.add(text)
            formatted_content += f"<h3>{text}</h3>\n"

    # Process paragraphs and other text containers
    seen_paragraphs = set()
    for element in content.find_all(['p', 'div']):
        text = element.text.strip()
        if (text 
            and len(text) > 30
            and text not in seen_paragraphs
            and not any(text in p for p in seen_paragraphs)
            and len(text.split()) > 5):
            seen_paragraphs.add(text)
            formatted_content += f"<p>{text}</p>\n"

    return formatted_content if formatted_content.strip() else None

def _extract_title(soup: BeautifulSoup) -> str:
    """Extract article title using multiple methods."""
    title_candidates = [
        soup.find('meta', {'property': 'og:title'}),
        soup.find('meta', {'name': 'twitter:title'}),
        soup.find('h1'),
        soup.find('title')
    ]

    for candidate in title_candidates:
        if candidate:
            title = candidate.get('content', '') if candidate.get('content') else candidate.text
            title = title.strip()
            if title and len(title) < 200:
                return title

    return 'Untitled Article'

def _extract_date(soup: BeautifulSoup) -> datetime:
    """Extract publication date using multiple methods."""
    date_candidates = [
        soup.find('meta', {'property': 'article:published_time'}),
        soup.find('meta', {'property': 'og:published_time'}),
        soup.find('time'),
        soup.find('meta', {'name': 'date'})
    ]

    for candidate in date_candidates:
        if candidate:
            date_str = candidate.get('content', '') or candidate.get('datetime', '')
            try:
                if date_str:
                    return datetime.fromisoformat(date_str.split('T')[0])
            except ValueError:
                continue

    return datetime.now()

def _extract_source(soup: BeautifulSoup, url: str) -> str:
    """Extract source name using multiple methods."""
    source_candidates = [
        soup.find('meta', {'property': 'og:site_name'}),
        soup.find('meta', {'name': 'application-name'})
    ]

    for candidate in source_candidates:
        if candidate:
            source = candidate.get('content', '').strip()
            if source:
                return source

    # Fallback to domain name
    domain = urlparse(url).netloc
    return domain.replace('www.', '')