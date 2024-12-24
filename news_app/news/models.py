from django.db import models

# Create your models here.
class NewsArticle(models.Model):
    title = models.CharField(max_length=255)
    summary = models.TextField(null=True, blank=True)
    source = models.CharField(max_length=100)
    url = models.URLField()
    published_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title