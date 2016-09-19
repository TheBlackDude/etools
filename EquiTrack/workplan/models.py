from jsonfield import JSONField
from django.db import models
from django.contrib.auth.models import User


from users.models import Section
from locations.models import Location
from partners.models import PartnerOrganization
from reports.models import ResultType


class Comment(models.Model):
    author = models.ForeignKey(User, related_name='comments')
    tagged_users = models.ManyToManyField(User, blank=True, related_name='+')
    timestamp = models.DateTimeField(auto_now_add=True)
    text = models.TextField()
    workplan = models.ForeignKey('Workplan', related_name='comments')


class Workplan(models.Model):
    STATUS = (
        ("On Track", "On Track"),
        ("Constrained", "Constrained"),
        ("No Progress", "No Progress"),
        ("Target Met", "Target Met"),
    )
    status = models.CharField(max_length=32, null=True, blank=True, choices=STATUS)
    result_structure = models.ForeignKey('reports.ResultStructure')


class WorkplanProject(models.Model):
    workplan = models.ForeignKey('Workplan', related_name='workplan_projects')


class ResultWorkplanProperty(models.Model):
    workplan = models.ForeignKey(Workplan)
    result_type = models.ForeignKey(ResultType)
    assumptions = models.TextField(null=True, blank=True)
    STATUS = (
        ("On Track","On Track"),
        ("Constrained","Constrained"),
        ("No Progress","No Progress"),
        ("Target Met","Target Met"),
    )
    status = models.CharField(max_length=255, null=True, blank=True, choices=STATUS)
    prioritized = models.BooleanField(default=False)
    metadata = JSONField(null=True, blank=True)
    other_partners = models.CharField(max_length=2048, null=True, blank=True)
    rr_funds = models.PositiveIntegerField(null=True, blank=True)
    or_funds = models.PositiveIntegerField(null=True, blank=True)
    ore_funds = models.PositiveIntegerField(null=True, blank=True)
    total_funds = models.PositiveIntegerField(null=True, blank=True)
    sections = models.ManyToManyField(Section)
    geotag = models.ManyToManyField(Location)
    partners = models.ManyToManyField(PartnerOrganization)
    responsible_persons = models.ManyToManyField(User)

    def save(self, *args, **kwargs):
        """
        Override save to calculate field total
        """
        self.total_funds = self.rr_funds + self.or_funds + self.ore_funds
        super(ResultWorkplanProperty, self).save(*args, **kwargs)


class CoverPage(models.Model):
    workplan_project = models.OneToOneField('WorkplanProject', related_name='cover_page')

    national_priority = models.CharField(max_length=255)
    responsible_government_entity = models.CharField(max_length=255)
    planning_assumptions = models.TextField()

    logo_width = models.IntegerField(null=True, blank=True)
    logo_height = models.IntegerField(null=True, blank=True)
    logo = models.ImageField(width_field='logo_width', height_field='logo_height', null=True, blank=True)


class CoverPageBudget(models.Model):
    cover_page = models.ForeignKey('CoverPage', related_name='budgets')

    date = models.CharField(max_length=64)
    total_amount = models.CharField(max_length=64)
    funded_amount = models.CharField(max_length=64)
    unfunded_amount = models.CharField(max_length=64)
