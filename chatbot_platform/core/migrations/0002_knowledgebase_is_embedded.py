# Generated by Django 5.1.5 on 2025-04-10 05:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='knowledgebase',
            name='is_embedded',
            field=models.BooleanField(default=False),
        ),
    ]
