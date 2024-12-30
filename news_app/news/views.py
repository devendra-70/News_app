from datetime import datetime
from django.shortcuts import render, redirect
from django.utils.dateparse import parse_date
from django.http import JsonResponse
from urllib.parse import urlparse
from django.views.decorators.http import require_http_methods
from .models import NewsSource, NewsArticle
from .utils.article_fetcher import fetch_article_content
import logging

logger = logging.getLogger(__name__)

def extract_publisher(url):
    """Extract publisher name from URL"""
    domain = urlparse(url).netloc
    domain = domain.replace('www.', '').replace('feeds.', '')
    parts = domain.split('.')
    return parts[0].title() if parts else ''

def settings_page(request):
    return render(request, 'news/settings.html')

@require_http_methods(["POST"])
def add_source(request):
    name = request.POST.get('name')
    links = request.POST.getlist('links[]')

    # Check if the name is provided
    if not name or name.strip() == '':
        return JsonResponse({'error': 'Source name is required'}, status=400)

    if NewsSource.objects.filter(name=name).exists():
        return JsonResponse({'error': 'Source already exists'}, status=400)

    source = NewsSource.objects.create(name=name)
    for link in links:
        if link.strip():
            # Instead of RSSLink, you would now directly store the source
            source.links.create(url=link.strip())

    return JsonResponse({'success': True})

@require_http_methods(["GET"])
def get_sources(request):
    sources = NewsSource.objects.prefetch_related('links').all()
    data = [{
        'id': source.id,
        'name': source.name,
        'links': [link.url for link in source.links.all()]
    } for source in sources]
    return JsonResponse({'sources': data})

@require_http_methods(["POST"])
def update_source(request, source_id):
    source = NewsSource.objects.get(id=source_id)
    name = request.POST.get('name')
    links = request.POST.getlist('links[]')

    if NewsSource.objects.filter(name=name).exclude(id=source_id).exists():
        return JsonResponse({'error': 'Source already exists'}, status=400)

    source.name = name
    source.save()

    # Update links for the source
    source.links.all().delete()
    for link in links:
        if link.strip():
            source.links.create(url=link.strip())

    return JsonResponse({'success': True})

@require_http_methods(["DELETE"])
def delete_source(request, source_id):
    try:
        source = NewsSource.objects.get(id=source_id)
        source.delete()
        return JsonResponse({'success': True})
    except NewsSource.DoesNotExist:
        return JsonResponse({'error': 'Source not found'}, status=404)

def home(request):
    from_date = request.GET.get('from', None)
    to_date = request.GET.get('to', None)
    source_filter = request.GET.get('source', None)
    category_filter = request.GET.get('category', None)

    if from_date:
        from_date = parse_date(from_date)
        from_date = datetime.combine(from_date, datetime.min.time())

    if to_date:
        to_date = parse_date(to_date)
        to_date = datetime.combine(to_date, datetime.max.time())

    news_articles = NewsArticle.objects.all()

    # Fetch the articles based on the source filter
    if source_filter:
        news_articles = news_articles.filter(source=source_filter)
    if category_filter:
        news_articles = news_articles.filter(category=category_filter)
    if from_date:
        news_articles = news_articles.filter(published_at__gte=from_date)
    if to_date:
        news_articles = news_articles.filter(published_at__lte=to_date)

    sources = NewsSource.objects.all()
    categories = NewsArticle.objects.values_list('category', flat=True).distinct()

    news_articles = news_articles.order_by('-published_at')

    if request.headers.get('HX-Request'):
        offset = int(request.GET.get('offset', 0))
        limit = 20
        more_articles = news_articles[offset:offset+limit]
        has_more = len(news_articles[offset+limit:offset+limit+1]) > 0

        articles_html = render(request, 'news/article_list.html', {
            'news_articles': more_articles
        }).content.decode('utf-8')

        return JsonResponse({
            'html': articles_html,
            'has_more': has_more
        })

    article_url = request.GET.get('article_url', None)
    if article_url:
        article_content = fetch_article_content(article_url)
        if article_content:
            article_content['word_count_display'] = f"{article_content.get('word_count', 0)} words"
            if article_content.get('author'):
                article_content['byline'] = f"By {article_content['author']}"
        return render(request, 'news/article_detail.html', {'article_content': article_content})

    initial_articles = news_articles[:20]
    return render(request, 'news/home.html', {
        'news_articles': initial_articles,
        'sources': sources,
        'categories': categories,
        'from_date': from_date.strftime('%Y-%m-%d') if from_date else '',
        'to_date': to_date.strftime('%Y-%m-%d') if to_date else '',
        'selected_source': source_filter,
        'selected_category': category_filter,
        'filter_applied': bool(from_date or to_date or source_filter or category_filter)
    })
