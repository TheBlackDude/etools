__author__ = 'jcranwellward'

import random

import logging
from django.conf import settings
from django.core import urlresolvers
from django.db import IntegrityError
from django.contrib.gis.db import models
from django.contrib.contenttypes.generic import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from cartodb import CartoDBAPIKey, CartoDBException
from smart_selects.db_fields import ChainedForeignKey

logger = logging.getLogger('locations.models')


class Governorate(models.Model):
    name = models.CharField(max_length=45L, unique=True)
    area = models.PolygonField(null=True, blank=True)

    objects = models.GeoManager()

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Region(models.Model):
    governorate = models.ForeignKey(Governorate)
    name = models.CharField(max_length=45L, unique=True)
    area = models.PolygonField(null=True, blank=True)

    objects = models.GeoManager()

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = 'Caza'
        ordering = ['name']


class Locality(models.Model):
    region = models.ForeignKey(Region)
    cad_code = models.CharField(max_length=11L)
    cas_code = models.CharField(max_length=11L)
    cas_code_un = models.CharField(max_length=11L)
    name = models.CharField(max_length=128L)
    cas_village_name = models.CharField(max_length=128L)
    area = models.PolygonField(null=True, blank=True)

    objects = models.GeoManager()

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = 'Cadastral/Locality'
        unique_together = ('name', 'cas_code_un')
        ordering = ['name']


class GatewayType(models.Model):
    name = models.CharField(max_length=64L, unique=True)

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return self.name


class Location(models.Model):

    name = models.CharField(max_length=254L)
    locality = models.ForeignKey(Locality)
    gateway = models.ForeignKey(GatewayType, verbose_name='Gateway type')
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    p_code = models.CharField(max_length=32L, blank=True, null=True)

    point = models.PointField()
    objects = models.GeoManager()

    def __unicode__(self):
        #TODO: Make generic
        return u'{} ({} {})'.format(
            self.name,
            self.gateway.name,
            "{}: {}".format(
                'CERD' if self.gateway.name == 'School' else 'P Code',
                self.p_code if self.p_code else ''
            )
        )

    @property
    def point_lat_long(self):
        return "Lat: {}, Long: {}".format(
            self.point.y,
            self.point.x
        )

    class Meta:
        unique_together = ('name', 'gateway', 'p_code')
        ordering = ['name']


class LinkedLocation(models.Model):
    """
    Generic model for linking locations to anything
    """
    governorate = models.ForeignKey(Governorate)
    region = ChainedForeignKey(
        Region,
        chained_field="governorate",
        chained_model_field="governorate",
        show_all=False,
        auto_choose=True,
    )
    locality = ChainedForeignKey(
        Locality,
        chained_field="region",
        chained_model_field="region",
        show_all=False,
        auto_choose=True,
    )
    location = ChainedForeignKey(
        Location,
        chained_field="locality",
        chained_model_field="locality",
        show_all=False,
        auto_choose=False,
        null=True, blank=True
    )

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    def __unicode__(self):
        desc = u'{} -> {} -> {}'.format(
            self.governorate.name,
            self.region.name,
            self.locality.name,
        )
        if self.location:
            desc = u'{} -> {} ({})'.format(
                desc,
                self.location.name,
                self.location.gateway.name
            )

        return desc


class CartoDBTable(models.Model):

    domain = models.CharField(max_length=254)
    api_key = models.CharField(max_length=254)
    table_name = models.CharField(max_length=254)
    location_type = models.ForeignKey(GatewayType)
    name_col = models.CharField(max_length=254, default='name')
    pcode_col = models.CharField(max_length=254, default='pcode')
    latitude_col = models.CharField(max_length=254, default='latitude')
    longitude_col = models.CharField(max_length=254, default='longitude')

    def update_sites_from_cartodb(self):

        client = CartoDBAPIKey(self.api_key, self.domain)

        sites_created = sites_updated = sites_not_added = 0
        try:
            sites = client.sql(
                'select * from {}'.format(self.table_name)
            )
        except CartoDBException as e:
            print ("CartoDB exception occured", e)
        else:

            for row in sites['rows']:
                pcode = row[self.pcode_col]
                cad_code = row['cad_code']
                site_name = row[self.name_col].encode('UTF-8')

                if not cad_code:
                    logger.warn("No cad code for: {}".format(site_name))
                    sites_not_added += 1
                    continue

                if not site_name or site_name.isspace():
                    logger.warn("No name for site with PCode: {}".format(pcode))
                    sites_not_added += 1
                    continue

                try:
                    cad = Locality.objects.get(cad_code=cad_code)
                except Locality.DoesNotExist:
                    logger.warn("No locality found for cad code: {}".format(cad_code))

                location, created = Location.objects.get_or_create(
                    gateway=self.location_type,
                    p_code=pcode,
                    locality=cad
                )
                if created:
                    sites_created += 1
                else:
                    sites_updated += 1

                location.name = site_name
                location.latitude = row[self.latitude_col]
                location.longitude = row[self.longitude_col]
                location.point = row['the_geom']

                try:
                    location.save()
                except IntegrityError as e:
                    logger.exception('')

                logger.info('{}: {} ({})'.format(
                    'Added' if created else 'Updated',
                    location.name,
                    self.location_type.name
                ))

        return sites_created, sites_updated, sites_not_added
