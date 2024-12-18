# Generated by Django 4.2.17 on 2024-12-15 13:05

import Home.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Home', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='books',
            name='id',
            field=models.BigAutoField(auto_created=True, default=1, primary_key=True, serialize=False, verbose_name='ID'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='books',
            name='Bid',
            field=models.CharField(default=Home.models.get_next_bid, max_length=3, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='issued',
            name='issued_bid',
            field=models.AutoField(primary_key=True, serialize=False),
        ),
    ]
