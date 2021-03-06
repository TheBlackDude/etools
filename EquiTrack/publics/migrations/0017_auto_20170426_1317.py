# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2017-04-26 13:17
from __future__ import unicode_literals

from datetime import date

from django.db import migrations


def fix_improper_effective_from_dates(apps, schema_editor):
    DSARate = apps.get_model('publics', 'DSARate')

    for rate in DSARate.objects.filter(effective_from_date__year__lt=2000):
        rate.effective_from_date = date(rate.effective_from_date.year + 2000,
                                        rate.effective_from_date.month,
                                        rate.effective_from_date.day)
        rate.save()


class Migration(migrations.Migration):

    dependencies = [
        ('publics', '0016_auto_20170426_1234'),
    ]

    operations = [
        migrations.RenameField(
            model_name='dsarate',
            old_name='eff_date',
            new_name='effective_from_date',
        ),
        migrations.RunPython(fix_improper_effective_from_dates),
    ]
