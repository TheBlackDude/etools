
from django.db import models
from django.contrib.auth.models import User
from . import BooleanChoice, TripStatus

class Currency(models.Model):
    # This will be populated from vision
    name = models.CharField(max_length=128)
    iso_4217 = models.CharField(max_length=3)


class AirlineCompany(models.Model):
    # This will be populated from vision
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=12)


class Travel(models.Model):
    status = models.CharField(max_length=10, choices=TripStatus.CHOICES)
    traveller = models.ForeignKey(User, related_name='travels')
    supervisor = models.ForeignKey(User, related_name='+')
    office = models.ForeignKey('users.Office', related_name='+')
    section = models.ForeignKey('users.Section', related_name='+')
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    purpose = models.CharField(max_length=120)
    international_travel = models.BooleanField(default=False)
    ta_required = models.BooleanField(default=True)
    reference_number = models.CharField(max_length=12)


class TravelActivity(models.Model):
    travel = models.ForeignKey('Travel', related_name='activities')
    travel_type = models.CharField(max_length=64)
    partner = models.ForeignKey('partners.PartnerOrganization', related_name='+')
    partnership = models.ForeignKey('partners.PCA')
    result = models.ForeignKey('reports.Result', related_name='+')
    location = models.ForeignKey('locations.Location', related_name='+')


class IteneraryItem(models.Model):
    travel = models.ForeignKey('Travel', related_name='itinerary')
    origin = models.CharField(max_length=255)
    destination = models.CharField(max_length=255)
    departure_date = models.DateTimeField()
    arrival_date = models.DateTimeField()
    dsa_region = models.CharField(max_length=255)
    overnight_travel = models.BooleanField(default=False)
    mode_of_travel = models.CharField(max_length=255)
    airline = models.ForeignKey('AirlineCompany')


class Expense(models.Model):
    travel = models.ForeignKey('Travel', related_name='expenses')
    type = models.CharField(max_length=64)
    document_currency = models.ForeignKey('Currency')
    account_currency = models.ForeignKey('Currency')
    amount = models.DecimalField(max_digits=10, decimal_places=4)


class Deduction(models.Model):
    travel = models.ForeignKey('Travel', related_name='deductions')
    date = models.DateField()
    breakfast = models.BooleanField(default=False)
    lunch = models.BooleanField(default=False)
    dinner = models.BooleanField(default=False)
    accomodation = models.BooleanField(default=False)
    no_dsa = models.BooleanField(default=False)

    @property
    def day_of_the_week(self):
        return self.date.strftime('%a')


class CostAssignment(models.Model):
    travel = models.ForeignKey('Travel', related_name='cost_assignments')
    wbs = models.ForeignKey('reports.Result', related_name='+')
    share = models.PositiveIntegerField()
    grant = models.ForeignKey('funds.Grant')
    # fund = models.ForeignKey()    # No idea where to connect


class Clearances(models.Model):
    travel = models.OneToOneField('Travel', related_name='clearances')
    medical_clearance = models.NullBooleanField(default=None, choices=BooleanChoice.CHOICES)
    security_clearance = models.NullBooleanField(default=None, choices=BooleanChoice.CHOICES)
    security_course = models.NullBooleanField(default=None, choices=BooleanChoice.CHOICES)