# Generated by Django 5.1.5 on 2025-04-06 03:59

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Book',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=255)),
                ('authors', models.JSONField(blank=True, default=list, null=True)),
                ('isbn', models.CharField(blank=True, max_length=20, null=True, unique=True)),
                ('publication_date', models.DateField(blank=True, null=True)),
                ('publisher', models.CharField(blank=True, max_length=255, null=True)),
                ('genres', models.JSONField(blank=True, default=list, null=True)),
                ('language', models.CharField(blank=True, max_length=50, null=True)),
                ('page_count', models.IntegerField(blank=True, null=True)),
            ],
            options={
                'db_table': 'api_book',
            },
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bio', models.TextField(blank=True, null=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'api_user_profile',
            },
        ),
    ]
