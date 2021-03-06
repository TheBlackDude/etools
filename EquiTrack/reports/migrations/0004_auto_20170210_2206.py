# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2017-02-10 20:06
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0003_auto_20161227_1953'),
    ]

    operations = [
        migrations.AddField(
            model_name='appliedindicator',
            name='means_of_verification',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='indicatorblueprint',
            name='unit',
            field=models.CharField(choices=[('number', 'number'), ('percentage', 'percentage'), ('yesno', 'yesno')], default='number', max_length=10),
        ),
    ]
