# views.py
from datetime import datetime
from django.shortcuts import render, redirect
from django.utils.dateparse import parse_date
from django.http import JsonResponse
from urllib.parse import urlparse
from django.views.decorators.http import require_http_methods
from .models import NewsSource, NewsArticle
from .utils.article_fetcher import fetch_article_content
import logging
from .utils.feed_parser import FeedParser
from django.db.models import Q
from django.core.paginator import Paginator

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


logger = logging.getLogger(__name__)

def home(request):
    """
    Main view for the news homepage. Handles article listing, filtering,
    infinite scrolling, and article detail views.
    """
    try:
        # Initialize feed parser if no articles exist
        if not NewsArticle.objects.exists():
            try:
                parser = FeedParser()
                parser.fetch_all_feeds()
            except Exception as e:
                logger.error(f"Error fetching feeds: {str(e)}")

        # Get filter parameters
        from_date = request.GET.get('from')
        to_date = request.GET.get('to')
        source_filter = request.GET.get('source')
        category_filter = request.GET.get('category')
        search_query = request.GET.get('search')

        # Base queryset
        news_articles = NewsArticle.objects.all()

        # Apply filters
        filters = Q()
        
        # Date filters
        if from_date:
            try:
                from_date = parse_date(from_date)
                from_date = datetime.combine(from_date, datetime.min.time())
                filters &= Q(published_at__gte=from_date)
            except ValueError as e:
                logger.warning(f"Invalid from_date format: {e}")

        if to_date:
            try:
                to_date = parse_date(to_date)
                to_date = datetime.combine(to_date, datetime.max.time())
                filters &= Q(published_at__lte=to_date)
            except ValueError as e:
                logger.warning(f"Invalid to_date format: {e}")

        # Source and category filters
        if source_filter:
            filters &= Q(source=source_filter)
        if category_filter:
            filters &= Q(category=category_filter)

        # Search filter
        if search_query:
            search_filters = Q(title__icontains=search_query) | \
                           Q(content__icontains=search_query) | \
                           Q(summary__icontains=search_query)
            filters &= search_filters

        # Apply all filters and order
        news_articles = news_articles.filter(filters).order_by('-published_at')

        # Get sources and categories for filters
        sources = NewsSource.objects.all()
        categories = NewsArticle.objects.values_list('category', flat=True)\
                                     .exclude(category='')\
                                     .exclude(category__isnull=True)\
                                     .distinct()

        # Handle AJAX load more requests
        if request.headers.get('HX-Request'):
            try:
                offset = int(request.GET.get('offset', 0))
                limit = 20
                paginator = Paginator(news_articles, limit)
                page_number = (offset // limit) + 1
                page = paginator.get_page(page_number)

                articles_html = render(request, 'news/article_list.html', {
                    'news_articles': page.object_list
                }).content.decode('utf-8')

                return JsonResponse({
                    'html': articles_html,
                    'has_more': page.has_next()
                })
            except Exception as e:
                logger.error(f"Error in AJAX request: {str(e)}")
                return JsonResponse({
                    'error': 'Failed to load more articles'
                }, status=500)

        # Handle article detail view
        article_url = request.GET.get('article_url')
        if article_url:
            try:
                article_content = fetch_article_content(article_url)
                if article_content:
                    article_content['word_count_display'] = (
                        f"{article_content.get('word_count', 0):,} words"
                    )
                    if article_content.get('author'):
                        article_content['byline'] = f"By {article_content['author']}"
                    
                    return render(request, 'news/article_detail.html', {
                        'article_content': article_content
                    })
                else:
                    logger.warning(f"No content fetched for URL: {article_url}")
                    return render(request, 'news/article_detail.html', {
                        'error': 'Unable to fetch article content'
                    })
            except Exception as e:
                logger.error(f"Error fetching article content: {str(e)}")
                return render(request, 'news/article_detail.html', {
                    'error': 'Error loading article'
                })

        # Initial page load
        initial_articles = news_articles[:20]
        total_count = news_articles.count()

        context = {
            'news_articles': initial_articles,
            'sources': sources,
            'categories': categories,
            'from_date': from_date if from_date else '',
            'to_date': to_date if to_date else '',
            'selected_source': source_filter,
            'selected_category': category_filter,
            'search_query': search_query,
            'total_count': total_count,
            'filter_applied': bool(from_date or to_date or source_filter or 
                                 category_filter or search_query)
        }

        return render(request, 'news/home.html', context)

    except Exception as e:
        logger.error(f"Unexpected error in home view: {str(e)}")
        return render(request, 'news/home.html', {
            'error': 'An unexpected error occurred'
        })