# Generated by Django 4.2.17 on 2024-12-18 08:15

import Home.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Home', '0008_alter_books_bid_alter_issued_issue_no'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='books',
            name='id',
        ),
        migrations.AlterField(
            model_name='books',
            name='Bid',
            field=models.IntegerField(default=Home.models.get_next_bid, primary_key=True, serialize=False, unique=True),
        ),
    ]
