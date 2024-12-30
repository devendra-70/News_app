# utils/article_fetcher.py
import requests
from bs4 import BeautifulSoup
import logging
from urllib.parse import urlparse
from datetime import datetime

logger = logging.getLogger(__name__)

def fetch_article_content(url):
    """
    Enhanced article content fetcher with multiple fallback methods
    """
    try:
        # Configure headers to mimic a browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }
        
        # Make the request with headers and longer timeout
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Parse with more lenient settings
        soup = BeautifulSoup(response.content, 'html.parser', from_encoding=response.encoding)
        
        # Clean the HTML first
        _clean_html(soup)
        
        # Extract content using multiple methods
        content = _extract_content(soup)
        if not content:
            logger.warning(f"Could not extract content for URL: {url}")
            return None
            
        # Extract metadata
        title = _extract_title(soup)
        published_date = _extract_date(soup)
        source = _extract_source(soup, url)
        
        # Construct the response
        return {
            'title': title,
            'content': content,
            'source': source,
            'published_at': published_date
        }
        
    except requests.RequestException as e:
        logger.error(f"Request failed for {url}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error processing {url}: {str(e)}", exc_info=True)
        return None

def _clean_html(soup):
    """Remove unwanted elements from the HTML"""
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

def _extract_content(soup):
    """Extract content using multiple fallback methods"""
    # List of possible content containers and their classes/IDs
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
        if found and len(found.text.strip()) > 100:  # Ensure there's substantial content
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
        if text and text not in seen_headings and len(text) < 200:  # Avoid very long headings
            seen_headings.add(text)
            formatted_content += f"<h3>{text}</h3>\n"
    
    # Process paragraphs and other text containers
    seen_paragraphs = set()
    for element in content.find_all(['p', 'div']):
        text = element.text.strip()
        # Check for meaningful paragraphs
        if (text 
            and len(text) > 30  # Minimum length
            and text not in seen_paragraphs  # No duplicates
            and not any(text in p for p in seen_paragraphs)  # Not subset of existing
            and len(text.split()) > 5):  # Minimum words
            seen_paragraphs.add(text)
            formatted_content += f"<p>{text}</p>\n"
    
    return formatted_content if formatted_content.strip() else None

def _extract_title(soup):
    """Extract article title using multiple methods"""
    title = None
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
            if title and len(title) < 200:  # Reasonable title length
                break
                
    return title or 'Untitled Article'

def _extract_date(soup):
    """Extract publication date using multiple methods"""
    date = None
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
                    date = datetime.fromisoformat(date_str.split('T')[0])
                    break
            except ValueError:
                continue
                
    return date or datetime.now()

def _extract_source(soup, url):
    """Extract source name using multiple methods"""
    source = None
    source_candidates = [
        soup.find('meta', {'property': 'og:site_name'}),
        soup.find('meta', {'name': 'application-name'})
    ]
    
    for candidate in source_candidates:
        if candidate:
            source = candidate.get('content', '').strip()
            if source:
                break
                
    if not source:
        # Fallback to domain name
        domain = urlparse(url).netloc
        source = domain.replace('www.', '')
        
    return source