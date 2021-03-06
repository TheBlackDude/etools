# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2017-04-24 12:06
from __future__ import unicode_literals

from datetime import datetime
from pytz import UTC

from django.db import migrations


def move_dsa_data(apps, schema_editor):
    fields_to_copy = ['dsa_amount_usd',
                      'dsa_amount_60plus_usd',
                      'dsa_amount_local',
                      'dsa_amount_60plus_local',
                      'room_rate',
                      'finalization_date',
                      'eff_date']

    DSARegion = apps.get_model('publics', 'DSARegion')
    DSARate = apps.get_model('publics', 'DSARate')

    for region in DSARegion.admin_objects.all():
        valid_from = datetime(region.eff_date.year, region.eff_date.month, region.eff_date.day, tzinfo=UTC)
        rate_kwargs = {'region': region,
                       'valid_from': valid_from}

        for key in fields_to_copy:
            rate_kwargs[key] = getattr(region, key)

        DSARate.objects.create(**rate_kwargs)


class Migration(migrations.Migration):

    dependencies = [
        ('publics', '0013_auto_20170424_1203'),
    ]

    operations = [
        migrations.RunPython(move_dsa_data),
    ]
