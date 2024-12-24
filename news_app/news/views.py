from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
from .models import NewsArticle
from .utils import fetch_news_from_api, fetch_news_from_rss

def home(request):
    # Fetch the latest news
    fetch_news_from_api()
    fetch_news_from_rss()

    # Get the 20 most recent articles, sorted by publication date
    news_articles = NewsArticle.objects.all().order_by('-published_at')[:20]

    return render(request, 'news/home.html', {'news_articles': news_articles})
