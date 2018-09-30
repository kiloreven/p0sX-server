# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-09-25 18:35
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pos', '0005_auto_20170902_1225'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='category',
            options={'verbose_name_plural': 'Categories'},
        ),
        migrations.AlterModelOptions(
            name='user',
            options={'permissions': (("update_credit", "Can update the credit limit on a user"),)},
        ),
    ]
