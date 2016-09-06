from datetime import datetime
from django.db import models
import django.contrib.postgres.fields as pgfields
from jsonfield import JSONField

from users.models import UserProfile, Section
from mptt.models import MPTTModel, TreeForeignKey
from locations.models import Location
from paintstore.fields import ColorPickerField
from model_utils.models import (
    TimeFramedModel,
    TimeStampedModel,
)

from django.utils.functional import cached_property


class CountryProgramme(models.Model):
    name = models.CharField(max_length=150)
    wbs = models.CharField(max_length=30, unique=True)
    from_date = models.DateField()
    to_date = models.DateField()

    @classmethod
    def current(cls):
        today = datetime.now()
        return cls.objects.get(to_date__gte=today, from_date__lt=today)


class ResultStructure(models.Model):

    name = models.CharField(max_length=150)
    country_programme = models.ForeignKey(CountryProgramme, null=True, blank=True)
    from_date = models.DateField()
    to_date = models.DateField()
    # TODO: add validation these dates should never extend beyond the country programme structure

    class Meta:
        ordering = ['name']
        unique_together = (("name", "from_date", "to_date"),)

    def __unicode__(self):
        return self.name

    @classmethod
    def current(cls):
        return ResultStructure.objects.order_by('to_date').last()


class ResultType(models.Model):
    OUTCOME = 'Outcome'
    OUTPUT = 'Output'
    ACTIVITY = 'Activity'
    SUBACTIVITY = 'Sub-Activity'

    NAME_CHOICES = (
        (OUTCOME, 'Outcome'),
        (OUTPUT, 'Output'),
        (ACTIVITY, 'Activity'),
        (SUBACTIVITY, 'Sub-Activity'),
    )
    name = models.CharField(max_length=150, unique=True, choices=NAME_CHOICES)

    def __unicode__(self):
        return self.name


class Sector(models.Model):

    name = models.CharField(max_length=45L, unique=True)
    description = models.CharField(
        max_length=256L,
        blank=True,
        null=True
    )
    alternate_id = models.IntegerField(
        blank=True,
        null=True
    )
    alternate_name = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    dashboard = models.BooleanField(
        default=False
    )
    color = ColorPickerField(null=True, blank=True)

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return u'{} {}'.format(
            self.alternate_id if self.alternate_id else '',
            self.name
        )

class ResultManager(models.Manager):
    def get_queryset(self):
        return super(ResultManager, self).get_queryset().select_related('country_programme', 'result_structure', 'result_type')


class Result(MPTTModel):

    result_structure = models.ForeignKey(ResultStructure, null=True, blank=True)
    country_programme = models.ForeignKey(CountryProgramme, null=True, blank=True)
    result_type = models.ForeignKey(ResultType)
    sector = models.ForeignKey(Sector, null=True, blank=True)
    name = models.TextField()
    code = models.CharField(max_length=50, null=True, blank=True)
    from_date = models.DateField(null=True, blank=True)
    to_date = models.DateField(null=True, blank=True)
    parent = TreeForeignKey(
        'self',
        null=True, blank=True,
        related_name='children',
        db_index=True
    )
    assumptions = models.TextField(null=True, blank=True)
    # Holds UserProfile ids. For tagging this solution is sufficient,
    # but it lacks integrity checking. Switch to M2M field if needed.
    users = pgfields.ArrayField(models.IntegerField(), default=list)

    # activity level attributes
    humanitarian_tag = models.BooleanField(default=False)
    wbs = models.CharField(max_length=50, null=True, blank=True)
    vision_id = models.CharField(max_length=10, null=True, blank=True)
    gic_code = models.CharField(max_length=8, null=True, blank=True)
    gic_name = models.CharField(max_length=255, null=True, blank=True)
    sic_code = models.CharField(max_length=8, null=True, blank=True)
    sic_name = models.CharField(max_length=255, null=True, blank=True)
    activity_focus_code = models.CharField(max_length=8, null=True, blank=True)
    activity_focus_name = models.CharField(max_length=255, null=True, blank=True)
    sections = models.ManyToManyField(Section)
    STATUS = (
        ("On Track","On Track"),
        ("Constrained","Constrained"),
        ("No Progress","No Progress"),
        ("Target Met","Target Met"),
    )
    status = models.CharField(max_length=255, null=True, blank=True, choices=STATUS)
    geotag = models.ManyToManyField(Location)
    prioritized = models.BooleanField(default=False)
    metadata = JSONField(null=True, blank=True)

    hidden = models.BooleanField(default=False)
    ram = models.BooleanField(default=False)

    objects = ResultManager()

    class Meta:
        ordering = ['name']
        unique_together = (('wbs', 'country_programme'),)

    @cached_property
    def result_name(self):
        return u'{} {}: {}'.format(
            self.code if self.code else u'',
            self.result_type.name,
            self.name
        )

    def __unicode__(self):
        return u'{} {}: {}'.format(
            self.code if self.code else u'',
            self.result_type.name,
            self.name
        )

    def valid_entry(self):
        if self.wbs:
            return self.wbs.startswith(self.country_programme.wbs)

    def save(self, *args, **kwargs):
        # TODO add a validator that makes sure that the current result wbs fits within the countryProgramme wbs
        if not self.wbs:
            self.wbs = None
        super(Result, self).save(*args, **kwargs)
        nodes = self.get_descendants()
        for node in nodes:
            if node.hidden is not self.hidden:
                node.hidden = self.hidden
                node.save()


class Milestone(models.Model):

    result = models.ForeignKey(Result, related_name="milestones")
    description = models.TextField()
    assumptions = models.TextField(null=True, blank=True)


class Goal(models.Model):

    result_structure = models.ForeignKey(
        ResultStructure, blank=True, null=True)
    sector = models.ForeignKey(Sector, related_name='goals')
    name = models.CharField(max_length=512L, unique=True)
    description = models.CharField(max_length=512L, blank=True)

    class Meta:
        verbose_name = 'CCC'
        ordering = ['name']

    def __unicode__(self):
        return self.name


class Unit(models.Model):
    type = models.CharField(max_length=45L, unique=True)

    class Meta:
        ordering = ['type']

    def __unicode__(self):
        return self.type


class Indicator(models.Model):

    sector = models.ForeignKey(
        Sector,
        blank=True, null=True
    )
    result_structure = models.ForeignKey(
        ResultStructure,
        blank=True, null=True
    )

    result = models.ForeignKey(Result, null=True, blank=True)
    name = models.CharField(max_length=1024)
    code = models.CharField(max_length=50, null=True, blank=True)
    unit = models.ForeignKey(Unit, null=True, blank=True)

    total = models.IntegerField(verbose_name='UNICEF Target', null=True, blank=True)
    sector_total = models.IntegerField(verbose_name='Sector Target', null=True, blank=True)
    current = models.IntegerField(null=True, blank=True, default=0)
    sector_current = models.IntegerField(null=True, blank=True)
    assumptions = models.TextField(null=True, blank=True)

    # RAM Info
    target = models.CharField(max_length=255, null=True, blank=True)
    baseline = models.CharField(max_length=255, null=True, blank=True)
    ram_indicator = models.BooleanField(default=False)

    view_on_dashboard = models.BooleanField(default=False)

    in_activity_info = models.BooleanField(default=False)
    activity_info_indicators = models.ManyToManyField(
        'activityinfo.Indicator',
    )

    class Meta:
        ordering = ['name']
        unique_together = (("name", "result", "sector"),)

    def __unicode__(self):
        return u'{} {} {}'.format(
            self.name,
            u'Baseline: {}'.format(self.baseline) if self.baseline else u'',
            u'Target: {}'.format(self.target) if self.target else u''
        )

    def programmed_amounts(self):
        from partners.models import PCA
        return self.resultchain_set.filter(
            partnership__status__in=[PCA.ACTIVE, PCA.IMPLEMENTED]
        )

    def programmed(self, result_structure=None):
        programmed = self.programmed_amounts()
        if result_structure:
            programmed = programmed.filter(
                partnership__result_structure=result_structure,

            )
        total = programmed.aggregate(models.Sum('target'))
        return total[total.keys()[0]] or 0

    def progress(self, result_structure=None):
        programmed = self.programmed_amounts()
        if result_structure:
            programmed = programmed.filter(
                partnership__result_structure=result_structure,

            )
        total = programmed.aggregate(models.Sum('current_progress'))
        return (total[total.keys()[0]] or 0) + self.current if self.current else 0
