# Register your models here.
# news/admin.py
from django.contrib import admin
from .models import NewsSource, RSSLink, FeedSource, NewsArticle,CustomFeed

admin.site.register(NewsSource)
admin.site.register(RSSLink)
admin.site.register(FeedSource)
admin.site.register(NewsArticle)
admin.site.register(CustomFeed)