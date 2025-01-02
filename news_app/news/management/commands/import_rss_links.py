import os
from django.core.management.base import BaseCommand
from news.models import NewsSource, RSSLink

class Command(BaseCommand):
    help = 'Import RSS links and News Sources from a text file'

    def handle(self, *args, **kwargs):
        file_path = 'news/rss-urls-1.txt'

        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'{file_path} not found.'))
            return

        with open(file_path, 'r') as file:
            for line in file:
                parts = line.strip().split()
                if len(parts) < 3:
                    self.stdout.write(self.style.WARNING(f'Skipping malformed line: {line.strip()}'))
                    continue

                # First word + second word as the news source
                news_source_name = parts[0] + ' ' + parts[1]
                rss_url = parts[2]

                # Create or get the NewsSource
                news_source, created = NewsSource.objects.get_or_create(name=news_source_name)
                
                # Create the RSSLink
                RSSLink.objects.create(source=news_source, url=rss_url)

                self.stdout.write(self.style.SUCCESS(f'Successfully added: {news_source_name} - {rss_url}'))
