# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-04-18 13:22
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pos', '0002_auto_20160418_0025'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='can_have_ingredients',
            field=models.BooleanField(default=False),
        ),
    ]