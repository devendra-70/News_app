import os
import sys

# Add the project directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from news_app.news.models import NewsSource, RSSLink
import django

# Set the default settings module for Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "news_app.settings")

# Initialize Django
django.setup()

def load_rss_links(file_path):
    if not os.path.exists(file_path):
        print(f"File {file_path} not found.")
        return

    with open(file_path, 'r') as file:
        for line in file:
            # Skip empty lines or comments
            if not line.strip() or line.startswith("#"):
                continue

            # Split line into parts
            try:
                country_category, rss_url = line.strip().split(maxsplit=1)
            except ValueError:
                print(f"Skipping malformed line: {line.strip()}")
                continue

            # Extract country and category from the country_category part
            try:
                country, category = country_category.split(maxsplit=1)
            except ValueError:
                print(f"Skipping malformed country/category: {country_category}")
                continue

            # Get or create NewsSource entry based on country and category
            news_source_name = f"{country} {category}"
            news_source, created = NewsSource.objects.get_or_create(name=news_source_name)

            # Create the RSSLink for this NewsSource
            rss_link, created = RSSLink.objects.get_or_create(
                source=news_source,
                url=rss_url
            )

            if created:
                print(f"Added RSS link: {rss_url} under source: {news_source_name}")
            else:
                print(f"RSS link already exists: {rss_url}")

# Usage
file_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'rss-urls-1.txt')
load_rss_links(file_path)
