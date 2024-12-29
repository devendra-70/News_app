from django.contrib import admin
from django.urls import path
from news.views import home  # Import both home and search views

urlpatterns = [
    path('admin/', admin.site.urls),  # Admin route
    path('', home, name='home'),     # Home route for the news app

]
