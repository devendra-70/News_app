from django.shortcuts import render
from .models import NewsArticle
from .utils import fetch_news_from_api
from datetime import datetime

def home(request):
    # Fetch the latest news without any specific query or date range
    fetch_news_from_api(query='')

    # Get the 20 most recent articles, sorted by publication date
    news_articles = NewsArticle.objects.all().order_by('-published_at')[:20]

    return render(request, 'news/home.html', {'news_articles': news_articles})

def search(request):
    query = request.GET.get('q', '')
    from_date = request.GET.get('from', None)
    to_date = request.GET.get('to', None)

    # If no query is provided, just show the latest news
    if query:
        fetch_news_from_api(query=query, from_date=from_date, to_date=to_date)

    # Get the 20 most recent articles matching the search query
    news_articles = NewsArticle.objects.all().order_by('-published_at')[:20]

    return render(request, 'news/home.html', {'news_articles': news_articles})
