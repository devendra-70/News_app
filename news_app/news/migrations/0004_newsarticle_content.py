# Generated by Django 5.1.2 on 2025-01-01 14:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0003_newssource_rsslink'),
    ]

    operations = [
        migrations.AddField(
            model_name='newsarticle',
            name='content',
            field=models.TextField(default='Default content goes here.'),
        ),
    ]
