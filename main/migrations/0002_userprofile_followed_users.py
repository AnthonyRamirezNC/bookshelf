# Generated by Django 5.1.5 on 2025-04-29 15:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='followed_users',
            field=models.ManyToManyField(blank=True, related_name='followers', to='main.userprofile'),
        ),
    ]
