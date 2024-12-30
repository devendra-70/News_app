from django.contrib import admin
from django.urls import path
from news import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('settings/', views.settings_page, name='settings'),
    path('news/sources/add/', views.add_source, name='add_source'),
    path('news/sources/', views.get_sources, name='get_sources'),
    path('news/sources/<int:source_id>/update/', views.update_source, name='update_source'),
    path('news/sources/<int:source_id>/delete/', views.delete_source, name='delete_source'),  # Add this line
]
