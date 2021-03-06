# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2017-02-15 15:06
from __future__ import unicode_literals

from django.db import migrations
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0006_remove_lowerresult_result_type'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='lowerresult',
            options={'ordering': ('-created',)},
        ),
        migrations.AddField(
            model_name='lowerresult',
            name='created',
            field=model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created'),
        ),
        migrations.AddField(
            model_name='lowerresult',
            name='modified',
            field=model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified'),
        ),
    ]
