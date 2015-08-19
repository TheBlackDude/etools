__author__ = 'jcranwellward'

import datetime

from django.db import models
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.generic import (
    GenericForeignKey, GenericRelation
)
from django.db.models.signals import post_save
from django.contrib.sites.models import Site

from filer.fields.file import FilerFileField
import reversion

from EquiTrack.mixins import AdminURLMixin
# from locations.models import LinkedLocation
from reports.models import WBS
from funds.models import Grant
from locations.models import Governorate
from . import emails


User = get_user_model()

BOOL_CHOICES = (
    (None, "N/A"),
    (True, "Yes"),
    (False, "No")
)


class Office(models.Model):
    name = models.CharField(max_length=254)
    zonal_chief = models.ForeignKey(
        User,
        blank=True, null=True,
        related_name='offices',
        verbose_name='Chief')
    location = models.ForeignKey(
        Governorate,
        blank=True, null=True,
    )

    def __unicode__(self):
        return self.name


class Trip(AdminURLMixin, models.Model):

    PLANNED = u'planned'
    SUBMITTED = u'submitted'
    APPROVED = u'approved'
    COMPLETED = u'completed'
    CANCELLED = u'cancelled'
    TRIP_STATUS = (
        (PLANNED, u"Planned"),
        (SUBMITTED, u"Submitted"),
        (APPROVED, u"Approved"),
        (COMPLETED, u"Completed"),
        (CANCELLED, u"Cancelled"),
    )

    PROGRAMME_MONITORING = u'programme_monitoring'
    ADVOCACY = u'advocacy'
    TECHNICAL_SUPPORT = u'technical_support'
    MEETING = u'meeting'
    DUTY_TRAVEL = u'duty_travel'
    HOME_LEAVE = u'home_leave'
    FAMILY_VISIT = u'family_visit'
    EDUCATION_GRANT = u'education_grant'
    STAFF_DEVELOPMENT = u'staff_development'
    STAFF_ENTITLEMENT = u'staff_entitlement'
    TRAVEL_TYPE = (
        (PROGRAMME_MONITORING, u'PROGRAMME MONITORING'),
        (ADVOCACY, u'ADVOCACY'),
        (TECHNICAL_SUPPORT, u'TECHNICAL SUPPORT'),
        (MEETING, u'MEETING'),
        (STAFF_DEVELOPMENT, u"STAFF DEVELOPMENT"),
        (STAFF_ENTITLEMENT, u"STAFF ENTITLEMENT"),
    )

    status = models.CharField(
        max_length=32L,
        choices=TRIP_STATUS,
        default=PLANNED,
    )
    cancelled_reason = models.CharField(
        max_length=254,
        blank=True, null=True,
        help_text='Please provide a reason if the mission is cancelled'
    )
    purpose_of_travel = models.CharField(
        max_length=254
    )
    travel_type = models.CharField(
        max_length=32L,
        choices=TRAVEL_TYPE,
        default=PROGRAMME_MONITORING
    )
    security_clearance_required = models.BooleanField(
        default=False,
        help_text='Do you need security clarance for this trip?'
    )
    international_travel = models.BooleanField(
        default=False,
        help_text='International travel will require approval from the representative'
    )
    from_date = models.DateField()
    to_date = models.DateField()

    pcas = models.ManyToManyField(
        u'partners.PCA',
        blank=True, null=True,
        verbose_name=u"Related PCAs"
    )
    partners = models.ManyToManyField(
        u'partners.PartnerOrganization',
        blank=True, null=True
    )
    main_observations = models.TextField(
        blank=True, null=True
    )

    ta_required = models.BooleanField(
        default=False,
        help_text='Is a Travel Authorisation (TA) is required?'
    )
    programme_assistant = models.ForeignKey(
        User,
        blank=True, null=True,
        verbose_name='Staff Responsible for TA',
        help_text='Needed if a Travel Authorisation (TA) is required',
        related_name='managed_trips'
    )

    ta_drafted = models.BooleanField(
        default=False,
        help_text='Has the TA been drafted in vision if applicable?'
    )
    ta_drafted_date = models.DateField(blank=True, null=True)
    ta_reference = models.CharField(max_length=254, blank=True, null=True)
    vision_approver = models.ForeignKey(
        User,
        blank=True, null=True,
        verbose_name='VISION Approver'
    )

    locations = GenericRelation('locations.LinkedLocation')

    owner = models.ForeignKey(User, verbose_name='Traveller', related_name='trips')
    section = models.ForeignKey('reports.Sector', blank=True, null=True)
    office = models.ForeignKey(Office, blank=True, null=True)
    travel_assistant = models.ForeignKey(
        User,
        blank=True, null=True,
        related_name='organised_trips',
        verbose_name='Travel focal point'
    )
    transport_booked = models.BooleanField(default=False)
    security_granted = models.BooleanField(default=False)

    supervisor = models.ForeignKey(User, related_name='supervised_trips')
    approved_by_supervisor = models.BooleanField(default=False)
    date_supervisor_approved = models.DateField(blank=True, null=True)

    budget_owner = models.ForeignKey(User, related_name='budgeted_trips', blank=True, null=True,)
    approved_by_budget_owner = models.BooleanField(default=False)
    date_budget_owner_approved = models.DateField(blank=True, null=True)

    human_resources = models.ForeignKey(User, related_name='certified_trips', blank=True, null=True)
    approved_by_human_resources = models.NullBooleanField(
        default=None,
        choices=BOOL_CHOICES,
        verbose_name='Certified by human resources',
        help_text='HR must approve all trips relating to training and staff development')
    date_human_resources_approved = models.DateField(blank=True, null=True)

    representative = models.ForeignKey(User, related_name='approved_trips', blank=True, null=True)
    representative_approval = models.NullBooleanField(default=None, choices=BOOL_CHOICES)
    date_representative_approved = models.DateField(blank=True, null=True)

    approved_date = models.DateField(blank=True, null=True)
    created_date = models.DateTimeField(auto_now_add=True)
    approved_email_sent = models.BooleanField(default=False)

    ta_trip_took_place_as_planned = models.BooleanField(
        default=False,
        verbose_name='Ta trip took place as attached',
        help_text='I certify that the travel took place exactly as per the attached Travel Authorization and'
                  ' that there were no changes to the itinerary'
    )
    ta_trip_repay_travel_allowance = models.BooleanField(
        default=False,
        help_text='I certify that I will repay any travel allowance to which I am not entitled'
    )
    ta_trip_final_claim = models.BooleanField(
        default=False,
        help_text='I authorize UNICEF to treat this as the FINAL Claim'
    )
    class Meta:
        ordering = ['-created_date']

    def __unicode__(self):
        return u'{}   {} - {}: {}'.format(
            self.reference(),
            self.from_date,
            self.to_date,
            self.purpose_of_travel
        )

    def reference(self):
        return '{}/{}-{}'.format(
            self.created_date.year,
            self.id,
            self.trip_revision
        ) if self.id else None
    reference.short_description = 'Reference'

    def outstanding_actions(self):
        return self.actionpoint_set.filter(
            status='open').count()

    @property
    def trip_revision(self):
        return reversion.get_for_object(self).count()

    @property
    def trip_overdue(self):
        if self.to_date < datetime.date.today() and self.status != Trip.COMPLETED:
            return True
        return False

    @property
    def requires_hr_approval(self):
        return self.travel_type in [
            # Trip.STAFF_DEVELOPMENT
        ]

    @property
    def requires_rep_approval(self):
        return self.international_travel

    @property
    def can_be_approved(self):
        if self.status != Trip.SUBMITTED:
            return False
        if not self.approved_by_supervisor:
            return False
        if self.requires_hr_approval\
        and not self.approved_by_human_resources:
            return False
        if self.requires_rep_approval\
        and not self.representative_approval:
            return False
        return True

    def save(self, **kwargs):
        # check if trip can be approved
        if self.can_be_approved:
            self.approved_date = datetime.datetime.today()
            self.status = Trip.APPROVED

        if self.status is not Trip.CANCELLED and self.cancelled_reason:
            self.status = Trip.CANCELLED

        super(Trip, self).save(**kwargs)

    @classmethod
    def get_all_trips(cls, user):
        super_trips = user.supervised_trips.filter(
            Q(status=Trip.APPROVED) | Q(status=Trip.SUBMITTED)
        )
        my_trips = user.trips.filter()
        return my_trips | super_trips

    @classmethod
    def send_trip_request(cls, sender, instance, created, **kwargs):
        """
        Trip emails alerts are sent at various stages...
        """
        # default list of recipients
        recipients = [
            instance.owner.email,
            instance.supervisor.email]

        if instance.budget_owner:
            if instance.budget_owner != instance.owner and instance.budget_owner != instance.supervisor:
                recipients.append(instance.budget_owner.email)

        if instance.status == Trip.SUBMITTED:
            emails.TripCreatedEmail(instance).send(
                instance.owner.email,
                *recipients
            )
            if instance.international_travel and instance.approved_by_supervisor:
                recipients.append(instance.representative.email)
                emails.TripRepresentativeEmail(instance).send(
                    instance.owner.email,
                    *recipients
                )

        elif instance.status == Trip.CANCELLED:
            # send an email to everyone if the trip is cancelled
            if instance.travel_assistant:
                recipients.append(instance.travel_assistant.email)
            for location in instance.locations.all():
                recipients.append(location.governorate.office.zonal_chief.email)
            emails.TripCancelledEmail(instance).send(
                instance.owner.email,
                *recipients
            )
        elif instance.status == Trip.APPROVED:
            if instance.travel_assistant and not instance.transport_booked:
                emails.TripTravelAssistantEmail(instance).send(
                    instance.owner.email,
                    instance.travel_assistant.email
                )

            if instance.ta_required and instance.programme_assistant and not instance.ta_drafted:
                emails.TripTAEmail(instance).send(
                    instance.owner.email,
                    instance.programme_assistant.email
                )

            if instance.ta_drafted and instance.vision_approver:
                emails.TripTADraftedEmail(instance).send(
                    instance.programme_assistant.email,
                    instance.vision_approver.email
                )

            if not instance.approved_email_sent:
                if instance.international_travel:
                    recipients.append(instance.representative.email)

                locations = instance.locations.all().values_list('governorate__id', flat=True)
                offices = Office.objects.filter(location_id__in=locations)
                recipients.extend(
                    [office.zonal_chief.email for office in offices if office.zonal_chief]
                )

                emails.TripApprovedEmail(instance).send(
                    instance.owner.email,
                    *recipients
                )
                instance.approved_email_sent = True
                instance.save()

        elif instance.status == Trip.COMPLETED:
            emails.TripCompletedEmail(instance).send(
                instance.owner.email,
                *recipients
            )

post_save.connect(Trip.send_trip_request, sender=Trip)


class TripFunds(models.Model):

    trip = models.ForeignKey(Trip)
    wbs = models.ForeignKey(WBS)
    grant = models.ForeignKey(Grant)
    amount = models.PositiveIntegerField(
        verbose_name='Percentage (%)'
    )

    class Meta:
        verbose_name = u'Funding'
        verbose_name_plural = u'Funding'


# class TripLocation(models.Model):
#     trip = models.ForeignKey(Trip)
#     governorate = models.ForeignKey(Governorate)
#     region = ChainedForeignKey(
#         Region,
#         chained_field="governorate",
#         chained_model_field="governorate",
#         show_all=False,
#         auto_choose=True,
#     )
#     locality = ChainedForeignKey(
#         Locality,
#         chained_field="region",
#         chained_model_field="region",
#         show_all=False,
#         auto_choose=True,
#         null=True, blank=True
#     )
#     location = ChainedForeignKey(
#         Location,
#         chained_field="locality",
#         chained_model_field="locality",
#         show_all=False,
#         auto_choose=False,
#         null=True, blank=True
#     )
#
#     content_type = models.ForeignKey(ContentType)
#     object_id = models.PositiveIntegerField()
#     content_object = GenericForeignKey('content_type', 'object_id')
#
#     def __unicode__(self):
#         desc = u'{} -> {}'.format(
#             self.governorate.name,
#             self.region.name,
#         )
#         if self.locality:
#             desc = u'{} -> {}'.format(
#                 desc,
#                 self.locality.name
#             )
#         if self.location:
#             desc = u'{} -> {} ({})'.format(
#                 desc,
#                 self.location.name,
#                 self.location.gateway.name
#             )
#
#         return desc


class TravelRoutes(models.Model):

    trip = models.ForeignKey(Trip)
    origin = models.CharField(max_length=254)
    destination = models.CharField(max_length=254)
    depart = models.DateTimeField()
    arrive = models.DateTimeField()
    remarks = models.CharField(max_length=254, null=True, blank=True)

    class Meta:
        verbose_name = u'Travel Itinerary'
        verbose_name_plural = u'Travel Itinerary'


class ActionPoint(models.Model):

    STATUS = (
        ('closed', 'Closed'),
        ('ongoing', 'On-going'),
        ('open', 'Open'),
        ('cancelled', 'Cancelled')
    )

    trip = models.ForeignKey(Trip)
    description = models.CharField(max_length=254)
    due_date = models.DateField()
    person_responsible = models.ForeignKey(User, related_name='for_action')
    persons_responsible = models.ManyToManyField(User, blank=True, null=True)
    actions_taken = models.TextField(blank=True, null=True)
    completed_date = models.DateField(blank=True, null=True)
    comments = models.TextField(blank=True, null=True)
    status = models.CharField(choices=STATUS, max_length=254, null=True, verbose_name='Status')
    created_date = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.description

    @property
    def overdue(self):
        return self.due_date <= datetime.date.today()

    @property
    def due_soon(self):
        delta = (self.due_date - datetime.date.today()).days
        return delta <= 2

    @property
    def traffic_color(self):
        if self.overdue:
            return 'red'
        elif self.due_soon:
            return 'yellow'
        else:
            return 'green'

    @classmethod
    def send_action(cls, sender, instance, created, **kwargs):

        recipients = [
            user.email
            for user in
            instance.persons_responsible.all()
        ]
        recipients.append(instance.trip.supervisor.email)

        if created:
            emails.TripActionPointCreated(instance).send(
                instance.trip.owner.email,
                *recipients
            )
        elif instance.status == 'closed':
            emails.TripActionPointClosed(instance).send(
                instance.trip.owner.email,
                *recipients
            )
        else:
            emails.TripActionPointUpdated(instance).send(
                instance.trip.owner.email,
                *recipients
            )


post_save.connect(ActionPoint.send_action, sender=ActionPoint)


class FileAttachment(models.Model):

    trip = models.ForeignKey(Trip, null=True, blank=True, related_name=u'files')
    type = models.ForeignKey(u'partners.FileType')
    file = FilerFileField(null=True, blank=True)
    report = models.FileField(
        upload_to=u'trip_reports'
    )

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    def __unicode__(self):
        return u'{}: {}'.format(
            self.type.name,
            self.report.name
        )
