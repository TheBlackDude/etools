# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2016-12-27 17:16
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('trips', '0002_remove_linkedpartner_result'),
        ('partners', '0003_auto_20161209_2030'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='resultchain',
            name='indicator',
        ),
        migrations.RemoveField(
            model_name='resultchain',
            name='partnership',
        ),
        migrations.RemoveField(
            model_name='resultchain',
            name='result',
        ),
        migrations.RemoveField(
            model_name='resultchain',
            name='result_type',
        ),
        migrations.DeleteModel(
            name='ResultChain',
        ),
    ]
