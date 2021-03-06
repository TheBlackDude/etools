# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2017-01-25 11:03
from __future__ import unicode_literals

from django.db import migrations
import django_fsm


class Migration(migrations.Migration):

    dependencies = [
        ('partners', '0009_auto_20170112_2051'),
    ]

    operations = [
        migrations.AlterField(
            model_name='intervention',
            name='status',
            field=django_fsm.FSMField(blank=True, choices=[('draft', 'Draft'), ('active', 'Active'), ('implemented', 'Implemented'), ('suspended', 'Suspended'), ('terminated', 'Terminated'), ('cancelled', 'Cancelled')], default='draft', help_text='Draft = In discussion with partner, Active = Currently ongoing, Implemented = completed, Terminated = cancelled or not approved', max_length=32),
        ),
    ]
