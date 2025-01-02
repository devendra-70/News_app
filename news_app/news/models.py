from django.db import models

class NewsSource(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class RSSLink(models.Model):
    source = models.ForeignKey(NewsSource, on_delete=models.CASCADE, related_name='links')
    url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.url

class FeedSource(models.Model):
    name = models.CharField(max_length=200)
    url = models.URLField(unique=True)
    feed_type = models.CharField(max_length=50, choices=[
        ('RSS', 'RSS'),
        ('ATOM', 'Atom'),
        ('XML', 'XML'),
        ('JSON', 'JSON')
    ])
    active = models.BooleanField(default=True)
    last_fetched = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name

class NewsArticle(models.Model):
    title = models.CharField(max_length=500)
    url = models.URLField(unique=True)
    summary = models.TextField()
    content = models.TextField(default="Default content goes here.")
    published_at = models.DateTimeField()
    source = models.CharField(max_length=200)
    category = models.CharField(max_length=100, default='General')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-published_at']

    def __str__(self):
        return self.title
