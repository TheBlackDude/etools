# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2017-01-26 21:36
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('partners', '0010_auto_20170125_1303'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='partnerorganization',
            name='hact_values',
        ),
    ]
