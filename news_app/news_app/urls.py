from django.contrib import admin
from django.urls import path
from news.views import home  # Import the `home` view directly

urlpatterns = [
    path('admin/', admin.site.urls),  # Admin route
    path('', home, name='home'),     # Home route for the news app
]
