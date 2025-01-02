from django.contrib import admin
from django.urls import path
from news import views

urlpatterns = [
    path('admin/', admin.site.urls),                        # Admin route
    path('', views.home, name='home'),                      # Home route for the news app
    path('settings/', views.settings_page, name='settings'),  # Settings page
    path('news/sources/add/', views.add_source, name='add_source'),  # Add source
    path('news/sources/', views.get_sources, name='get_sources'),  # List sources
    path('news/sources/<int:source_id>/update/', views.update_source, name='update_source'),  # Update source
    path('news/sources/<int:source_id>/delete/', views.delete_source, name='delete_source'),  # Delete source
    path('news/article/', views.fetch_article_content, name='fetch_article_content'),  # Article content
]
