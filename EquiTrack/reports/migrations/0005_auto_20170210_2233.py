# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2017-02-10 20:33
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0004_auto_20170210_2206'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='lowerresult',
            name='in_kind_amount',
        ),
        migrations.RemoveField(
            model_name='lowerresult',
            name='level',
        ),
        migrations.RemoveField(
            model_name='lowerresult',
            name='lft',
        ),
        migrations.RemoveField(
            model_name='lowerresult',
            name='parent',
        ),
        migrations.RemoveField(
            model_name='lowerresult',
            name='partner_contribution',
        ),
        migrations.RemoveField(
            model_name='lowerresult',
            name='quarters',
        ),
        migrations.RemoveField(
            model_name='lowerresult',
            name='rght',
        ),
        migrations.RemoveField(
            model_name='lowerresult',
            name='tree_id',
        ),
        migrations.RemoveField(
            model_name='lowerresult',
            name='unicef_cash',
        ),
    ]