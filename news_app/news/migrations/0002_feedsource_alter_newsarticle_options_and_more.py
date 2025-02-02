# Generated by Django 5.1.2 on 2024-12-29 10:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='FeedSource',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('url', models.URLField(unique=True)),
                ('feed_type', models.CharField(choices=[('RSS', 'RSS'), ('ATOM', 'Atom'), ('XML', 'XML'), ('JSON', 'JSON')], max_length=50)),
                ('active', models.BooleanField(default=True)),
                ('last_fetched', models.DateTimeField(blank=True, null=True)),
            ],
        ),
        migrations.AlterModelOptions(
            name='newsarticle',
            options={'ordering': ['-published_at']},
        ),
        migrations.AddField(
            model_name='newsarticle',
            name='category',
            field=models.CharField(default='General', max_length=100),
        ),
        migrations.AlterField(
            model_name='newsarticle',
            name='source',
            field=models.CharField(max_length=200),
        ),
        migrations.AlterField(
            model_name='newsarticle',
            name='summary',
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name='newsarticle',
            name='title',
            field=models.CharField(max_length=500),
        ),
        migrations.AlterField(
            model_name='newsarticle',
            name='url',
            field=models.URLField(unique=True),
        ),
    ]
