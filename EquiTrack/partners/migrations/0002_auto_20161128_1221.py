# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2016-11-28 10:21
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import django.db.models.manager


class Migration(migrations.Migration):

    dependencies = [
        ('partners', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelManagers(
            name='agreement',
            managers=[
                ('view_objects', django.db.models.manager.Manager()),
            ],
        ),
        migrations.AddField(
            model_name='agreement',
            name='partner_staff_members',
            field=models.ManyToManyField(blank=True, related_name='staff_members', to='partners.PartnerStaffMember'),
        ),
        migrations.AddField(
            model_name='agreement',
            name='status',
            field=models.CharField(blank=True, choices=[(b'draft', b'Draft'), (b'active', b'Active'), (b'ended', b'Ended'), (b'suspended', b'Suspended'), (b'terminated', b'Terminated')], max_length=32L),
        ),
        migrations.AlterField(
            model_name='partnerstaffmember',
            name='partner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='staff_members', to='partners.PartnerOrganization'),
        ),
        migrations.AlterField(
            model_name='pca',
            name='status',
            field=models.CharField(blank=True, choices=[('in_process', 'In Process'), ('active', 'Active'), ('implemented', 'Implemented'), ('cancelled', 'Cancelled'), ('suspended', 'Suspended'), ('terminated', 'Terminated')], default='in_process', help_text='In Process = In discussion with partner, Active = Currently ongoing, Implemented = completed, Cancelled = cancelled or not approved', max_length=32),
        ),
        migrations.AlterField(
            model_name='pcagrant',
            name='partnership',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='grants', to='partners.PCA'),
        ),
    ]
