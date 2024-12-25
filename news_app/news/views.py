from datetime import datetime
from django.shortcuts import render
from django.utils.dateparse import parse_date
from .models import NewsArticle
from .utils import fetch_news_from_api, fetch_news_from_rss
import logging

# Set up logging
logger = logging.getLogger(__name__)

def home(request):
    # Get the date filters from the request
    from_date = request.GET.get('from', None)
    to_date = request.GET.get('to', None)

    # Convert the string dates to datetime objects if they are provided
    if from_date:
        from_date = parse_date(from_date)  # Convert to datetime.date object
        # Set the time of the from_date to the start of the day (00:00:00)
        from_date = datetime.combine(from_date, datetime.min.time())
        logger.debug(f"From date: {from_date}")
    if to_date:
        to_date = parse_date(to_date)  # Convert to datetime.date object
        # Set the time of the to_date to the end of the day (23:59:59)
        to_date = datetime.combine(to_date, datetime.max.time())
        logger.debug(f"To date: {to_date}")

    # Fetch the latest news from both API and RSS sources
    fetch_news_from_api(query='')
    fetch_news_from_rss()

    # Filter articles by date range if provided
    news_articles = NewsArticle.objects.all()

    if from_date:
        news_articles = news_articles.filter(published_at__gte=from_date)
        logger.debug(f"Filtering by from_date >= {from_date}")
    if to_date:
        news_articles = news_articles.filter(published_at__lte=to_date)
        logger.debug(f"Filtering by to_date <= {to_date}")

    # Get the 20 most recent articles, sorted by publication date
    news_articles = news_articles.order_by('-published_at')[:100]

    # Log the final query to check if it's working
    for article in news_articles:
        logger.debug(f"Article: {article.title}, Published at: {article.published_at}")

    return render(request, 'news/home.html', {
        'news_articles': news_articles,
        'from_date': from_date.strftime('%Y-%m-%d') if from_date else '',
        'to_date': to_date.strftime('%Y-%m-%d') if to_date else '',
        'filter_applied': True if from_date or to_date else False
    })


def search(request):
    # Get the search query and date filters from the request
    query = request.GET.get('q', '')
    from_date = request.GET.get('from', None)
    to_date = request.GET.get('to', None)

    # Convert the string dates to datetime objects if they are provided
    if from_date:
        from_date = parse_date(from_date)  # Convert to datetime.date object
        # Set the time of the from_date to the start of the day (00:00:00)
        from_date = datetime.combine(from_date, datetime.min.time())
    if to_date:
        to_date = parse_date(to_date)  # Convert to datetime.date object
        # Set the time of the to_date to the end of the day (23:59:59)
        to_date = datetime.combine(to_date, datetime.max.time())

    # Log the dates for debugging
    logger.debug(f"Search query: {query}, From date: {from_date}, To date: {to_date}")

    # Fetch news from API based on the search query and date filters
    if query or from_date or to_date:
        fetch_news_from_api(query=query, from_date=from_date, to_date=to_date)
    
    # Fetch RSS news (RSS doesn't support search, so fetch the latest entries)
    fetch_news_from_rss()

    # Filter articles by search query and date range
    news_articles = NewsArticle.objects.all()

    if query:
        news_articles = news_articles.filter(title__icontains=query)
    if from_date:
        news_articles = news_articles.filter(published_at__gte=from_date)
    if to_date:
        news_articles = news_articles.filter(published_at__lte=to_date)

    # Sort the filtered articles by publication date and limit to 20
    news_articles = news_articles.order_by('-published_at')[:100]

    # Log the final query to check if it's working
    for article in news_articles:
        logger.debug(f"Article: {article.title}, Published at: {article.published_at}")

    return render(request, 'news/home.html', {
        'news_articles': news_articles,
        'from_date': from_date.strftime('%Y-%m-%d') if from_date else '',
        'to_date': to_date.strftime('%Y-%m-%d') if to_date else '',
        'filter_applied': True if from_date or to_date else False,
        'query': query
    })
