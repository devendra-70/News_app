# views.py
from datetime import datetime
from django.shortcuts import render
from django.utils.dateparse import parse_date
from .models import NewsArticle
from .utils.feed_parser import FeedParser  # Fixed import statement
import logging

logger = logging.getLogger(__name__)

def home(request):
    # Get the date filters from the request
    from_date = request.GET.get('from', None)
    to_date = request.GET.get('to', None)
    source_filter = request.GET.get('source', None)
    category_filter = request.GET.get('category', None)
    
    # Convert the string dates to datetime objects if they are provided
    if from_date:
        from_date = parse_date(from_date)
        from_date = datetime.combine(from_date, datetime.min.time())
        logger.debug(f"From date: {from_date}")
    
    if to_date:
        to_date = parse_date(to_date)
        to_date = datetime.combine(to_date, datetime.max.time())
        logger.debug(f"To date: {to_date}")

    # Initialize feed parser and fetch latest news
    parser = FeedParser()
    parser.fetch_all_feeds()

    # Filter articles
    news_articles = NewsArticle.objects.all()
    
    if from_date:
        news_articles = news_articles.filter(published_at__gte=from_date)
    if to_date:
        news_articles = news_articles.filter(published_at__lte=to_date)
    if source_filter:
        news_articles = news_articles.filter(source=source_filter)
    if category_filter:
        news_articles = news_articles.filter(category=category_filter)

    # Get unique sources and categories for filters
    sources = NewsArticle.objects.values_list('source', flat=True).distinct()
    categories = NewsArticle.objects.values_list('category', flat=True).distinct()

    # Get the 200 most recent articles, sorted by publication date
    news_articles = news_articles.order_by('-published_at')[:200]

    return render(request, 'news/home.html', {
        'news_articles': news_articles,
        'sources': sources,
        'categories': categories,
        'from_date': from_date.strftime('%Y-%m-%d') if from_date else '',
        'to_date': to_date.strftime('%Y-%m-%d') if to_date else '',
        'selected_source': source_filter,
        'selected_category': category_filter,
        'filter_applied': bool(from_date or to_date or source_filter or category_filter)
    })