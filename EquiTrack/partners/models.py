from __future__ import absolute_import

__author__ = 'jcranwellward'

import json
import datetime
from copy import deepcopy

import requests
import reversion
from django.conf import settings
from django.db import models, transaction
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.db.models import Sum

from filer.fields.file import FilerFileField
from smart_selects.db_fields import ChainedForeignKey
from model_utils.models import (
    TimeFramedModel,
    TimeStampedModel,
)
from model_utils import Choices

from EquiTrack.utils import get_changeform_link
from EquiTrack.mixins import AdminURLMixin
from funds.models import Grant
from reports.models import (
    ResultStructure,
    IntermediateResult,
    Rrp5Output,
    Indicator,
    Activity,
    Sector,
    Goal,
    WBS,
    ResultType,
    Result)
from locations.models import (
    Governorate,
    Locality,
    Location,
    Region,
)
from supplies.models import SupplyItem
from . import emails

User = get_user_model()


class PartnerOrganization(models.Model):

    NATIONAL = u'national'
    INTERNATIONAL = u'international'
    UNAGENCY = u'un-agency'
    PARTNER_TYPES = (
        (NATIONAL, u"National"),
        (INTERNATIONAL, u"International"),
        (UNAGENCY, u"UN Agency"),
    )

    type = models.CharField(
        max_length=50,
        choices=PARTNER_TYPES,
        default=NATIONAL
    )
    name = models.CharField(
        max_length=255,
        unique=True
    )
    description = models.CharField(
        max_length=256L,
        blank=True
    )
    address = models.TextField(
        blank=True,
        null=True
    )
    email = models.CharField(
        max_length=255,
        blank=True
    )
    contact_person = models.CharField(
        max_length=255,
        blank=True
    )
    phone_number = models.CharField(
        max_length=32L,
        blank=True
    )
    vendor_number = models.BigIntegerField(
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
    activity_info_partner = models.ForeignKey(
        'activityinfo.Partner',
        blank=True, null=True
    )

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return self.name


class Assessment(models.Model):

    SFMC = u'checklist'
    MICRO = u'micro'
    MACRO = u'macro'
    HIGH = u'high'
    SIGNIFICANT = u'significant'
    MODERATE = u'moderate'
    LOW = u'low'
    ASSESSMENT_TYPES = (
        (SFMC, u"Simplified financial management checklist"),
        (MICRO, u"Micro-Assessment"),
        (MACRO, u"Macro-Assessment"),
    )
    RISK_RATINGS = (
        (HIGH, u'High'),
        (SIGNIFICANT, u'Significant'),
        (MODERATE, u'Moderate'),
        (LOW, u'Low'),
    )

    partner = models.ForeignKey(
        PartnerOrganization
    )
    type = models.CharField(
        max_length=50,
        choices=ASSESSMENT_TYPES,
    )
    previous_value_with_UN = models.IntegerField(
        default=0,
        help_text=u'Value of agreements with other '
                  u'UN agencies in the last 5 years'
    )
    names_of_other_agencies = models.CharField(
        max_length=255,
        blank=True, null=True,
        help_text=u'List the names of the other '
                  u'agencies they have worked with'
    )
    expected_budget = models.IntegerField()
    notes = models.CharField(
        max_length=255,
        blank=True, null=True,
        verbose_name=u'Special requests',
        help_text=u'Note any special requests to be '
                  u'considered during the assessment'
    )
    requested_date = models.DateField(
        auto_now_add=True
    )
    requesting_officer = models.ForeignKey(
        'auth.User',
        related_name='requested_assessments'
    )
    approving_officer = models.ForeignKey(
        'auth.User',
        blank=True, null=True
    )
    planned_date = models.DateField(
        blank=True, null=True
    )
    completed_date = models.DateField(
        blank=True, null=True
    )
    rating = models.CharField(
        max_length=50,
        choices=RISK_RATINGS,
        default=HIGH,
    )
    report = FilerFileField(
        blank=True, null=True
    )

    def __unicode__(self):
        return u'{type}: {partner} {rating} {date}'.format(
            type=self.type,
            partner=self.partner.name,
            rating=self.rating,
            date=self.completed_date.strftime("%d-%m-%Y") if
            self.completed_date else u'NOT COMPLETED'
        )

    def download_url(self):
        if self.report:
            return u'<a class="btn btn-primary default" ' \
                   u'href="{}" >Download</a>'.format(self.report.file.url)
        return u''
    download_url.allow_tags = True
    download_url.short_description = 'Download Report'


class Recommendation(models.Model):

    PARTNER = u'partner'
    FUNDS = u'funds'
    STAFF = u'staff'
    POLICY = u'policy'
    INT_AUDIT = u'int-audit'
    EXT_AUDIT = u'ext-audit'
    REPORTING = u'reporting'
    SYSTEMS = u'systems'
    SUBJECT_AREAS = (
        (PARTNER, u'Implementing Partner'),
        (FUNDS, u'Funds Flow'),
        (STAFF, u'Staffing'),
        (POLICY, u'Acct Policies & Procedures'),
        (INT_AUDIT, u'Internal Audit'),
        (EXT_AUDIT, u'External Audit'),
        (REPORTING, u'Reporting and Monitoring'),
        (SYSTEMS, u'Information Systems'),
    )

    assessment = models.ForeignKey(Assessment)
    subject_area = models.CharField(max_length=50, choices=SUBJECT_AREAS)
    description = models.CharField(max_length=254)
    level = models.CharField(max_length=50, choices=Assessment.RISK_RATINGS,
                             verbose_name=u'Priority Flag')
    closed = models.BooleanField(default=False, verbose_name=u'Closed?')
    completed_date = models.DateField(blank=True, null=True)

    @classmethod
    def send_action(cls, sender, instance, created, **kwargs):
        pass

    class Meta:
        verbose_name = 'Key recommendation'
        verbose_name_plural = 'Key recommendations'


class Agreement(TimeFramedModel, TimeStampedModel):

    PCA = u'PCA'
    AWP = u'AWP'
    AGREEMENT_TYPES = (
        (PCA, u"Partner Cooperation Agreement"),
        #(AWP, u"Annual Work Plan"),
    )

    partner = models.ForeignKey(PartnerOrganization)
    agreement_type = models.CharField(
        max_length=10,
        choices=AGREEMENT_TYPES
    )

    attached_agreement = models.FileField(
        upload_to=u'agreements',
        blank=True,
    )

    signed_by_unicef_date = models.DateField(null=True, blank=True)
    signed_by = models.ForeignKey(
        User,
        related_name='signed_pcas',
        null=True, blank=True
    )

    signed_by_partner_date = models.DateField(null=True, blank=True)
    partner_first_name = models.CharField(max_length=64L, blank=True)
    partner_last_name = models.CharField(max_length=64L, blank=True)
    partner_email = models.CharField(max_length=128L, blank=True)

    def __unicode__(self):
        return u'{} for {}'.format(
            self.agreement_type,
            self.partner.name
        )


class PCA(AdminURLMixin, models.Model):

    IN_PROCESS = u'in_process'
    ACTIVE = u'active'
    IMPLEMENTED = u'implemented'
    CANCELLED = u'cancelled'
    PCA_STATUS = (
        (IN_PROCESS, u"In Process"),
        (ACTIVE, u"Active"),
        (IMPLEMENTED, u"Implemented"),
        (CANCELLED, u"Cancelled"),
    )
    PD = u'pd'
    MOU = u'mou'
    SSFA = u'ssfa'
    IC = u'ic'
    DCT = u'dct'
    PARTNERSHIP_TYPES = (
        (PD, u'Programme Document'),
        (MOU, u'Memorandum of Understanding'),
        (SSFA, u'Small Scale Funding Agreement'),
        (IC, u'Institutional Contract'),
        (DCT, u'Government Transfer'),
    )

    partner = models.ForeignKey(PartnerOrganization)
    agreement = ChainedForeignKey(
        Agreement,
        chained_field="partner",
        chained_model_field="partner",
        show_all=False,
        auto_choose=True,
        blank=True, null=True,
    )
    partnership_type = models.CharField(
        choices=PARTNERSHIP_TYPES,
        default=PD,
        blank=True, null=True,
        max_length=255
    )
    result_structure = models.ForeignKey(
        ResultStructure,
        blank=True, null=True,
        help_text=u'Which result structure does this partnership report under?'
    )
    number = models.CharField(max_length=45L, blank=True)
    title = models.CharField(max_length=256L)
    status = models.CharField(
        max_length=32L,
        blank=True,
        choices=PCA_STATUS,
        default=u'in_process',
        help_text=u'In Process = In discussion with partner, '
                  u'Active = Currently ongoing, '
                  u'Implemented = completed, '
                  u'Cancelled = cancelled or not approved'
    )
    start_date = models.DateField(
        null=True, blank=True,
        help_text=u'The date the partnership will start'
    )
    end_date = models.DateField(
        null=True, blank=True,
        help_text=u'The date the partnership will end'
    )
    initiation_date = models.DateField(
        help_text=u'The date when planning began with the partner'

    )
    submission_date = models.DateField(
        help_text=u'The date the partnership was submitted to the PRC',
        null=True, blank=True,
    )
    signed_by_unicef_date = models.DateField(null=True, blank=True)
    signed_by_partner_date = models.DateField(null=True, blank=True)

    # contacts
    unicef_mng_first_name = models.CharField(max_length=64L, blank=True)
    unicef_mng_last_name = models.CharField(max_length=64L, blank=True)
    unicef_mng_email = models.CharField(max_length=128L, blank=True)
    unicef_managers = models.ManyToManyField('auth.User', blank=True)

    partner_mng_first_name = models.CharField(max_length=64L, blank=True)
    partner_mng_last_name = models.CharField(max_length=64L, blank=True)
    partner_mng_email = models.CharField(max_length=128L, blank=True)
    partner_mng_phone = models.CharField(max_length=64L, blank=True)

    partner_focal_first_name = models.CharField(max_length=64L, blank=True)
    partner_focal_last_name = models.CharField(max_length=64L, blank=True)
    partner_focal_email = models.CharField(max_length=128L, blank=True)
    partner_focal_phone = models.CharField(max_length=64L, blank=True)

    # budget
    partner_contribution_budget = models.IntegerField(null=True, blank=True, default=0)
    unicef_cash_budget = models.IntegerField(null=True, blank=True, default=0)
    in_kind_amount_budget = models.IntegerField(null=True, blank=True, default=0)
    cash_for_supply_budget = models.IntegerField(null=True, blank=True, default=0)
    total_cash = models.IntegerField(null=True, blank=True, verbose_name='Total Budget', default=0)

    # meta fields
    sectors = models.CharField(max_length=255, null=True, blank=True)
    current = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    amendment = models.BooleanField(default=False)
    amended_at = models.DateTimeField(null=True)
    amendment_number = models.IntegerField(default=0)
    original = models.ForeignKey('PCA', null=True, related_name='amendments')

    class Meta:
        verbose_name = 'Partnership'
        verbose_name_plural = 'Partnerships'
        ordering = ['-number', 'amendment']

    def __unicode__(self):
        title = u'{}: {}'.format(
            self.partner.name,
            self.number
        )
        if self.amendment:
            title = u'{} (Amendment: {})'.format(
                title, self.amendment_number
            )
        return title

    @property
    def sector_children(self):
        sectors = self.pcasector_set.all().values_list('sector__id', flat=True)
        return Sector.objects.filter(id__in=sectors)

    @property
    def sector_id(self):
        if self.sector_children:
            return self.sector_children[0].id
        return 0

    @property
    def sector_names(self):
        return u', '.join(self.sector_children.values_list('name', flat=True))

    @property
    def sum_budget(self):
        total_sum = PCA.objects.filter(number=self.number).aggregate(Sum("total_cash"))
        return total_sum.values()[0]

    def total_unicef_contribution(self):
        cash = self.unicef_cash_budget if self.unicef_cash_budget else 0
        in_kind = self.in_kind_amount_budget if self.in_kind_amount_budget else 0
        return cash + in_kind
    total_unicef_contribution.short_description = 'Total Unicef contribution budget'

    def save(self, **kwargs):
        """
        Calculate total cash on save
        """
        partner_budget = self.partner_contribution_budget \
            if self.partner_contribution_budget else 0
        self.total_cash = partner_budget + self.total_unicef_contribution()

        super(PCA, self).save(**kwargs)

    @classmethod
    def get_active_partnerships(cls):
        return cls.objects.filter(current=True, status=cls.ACTIVE)

    @classmethod
    def send_changes(cls, sender, instance, created, **kwargs):
        # send emails to managers on changes
        manager, created = Group.objects.get_or_create(
            name=u'Partnership Manager'
        )
        managers = manager.user_set.all()  # | instance.unicef_managers.all()
        recipients = [user.email for user in managers]

        if created:  # new partnership
            emails.PartnershipCreatedEmail(instance).send(
                settings.DEFAULT_FROM_EMAIL,
                *recipients
            )

        else:  # change to existing
            emails.PartnershipUpdatedEmail(instance).send(
                settings.DEFAULT_FROM_EMAIL,
                *recipients
            )


post_save.connect(PCA.send_changes, sender=PCA)


class PCAGrant(models.Model):
    """
    Links a grant to a partnership with a specified amount
    """
    pca = models.ForeignKey(PCA)
    grant = models.ForeignKey(Grant)
    funds = models.IntegerField(null=True, blank=True)
    #TODO: Add multi-currency support

    class Meta:
        ordering = ['-funds']

    def __unicode__(self):
        return self.grant


class GwPCALocation(models.Model):
    """
    Links a location to a partnership
    """
    pca = models.ForeignKey(PCA, related_name='locations')
    sector = models.ForeignKey(Sector, null=True, blank=True)
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
        null=True,
        blank=True
    )
    location = ChainedForeignKey(
        Location,
        chained_field="locality",
        chained_model_field="locality",
        show_all=False,
        auto_choose=True,
        null=True,
        blank=True
    )
    tpm_visit = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Partnership Location'

    def __unicode__(self):
        return u'{} -> {}{}{}'.format(
            self.governorate.name,
            self.region.name,
            u'-> {}'.format(self.locality.name) if self.locality else u'',
            self.location.__unicode__() if self.location else u'',
        )

    def view_location(self):
        return get_changeform_link(self)
    view_location.allow_tags = True
    view_location.short_description = 'View Location'


class PCASector(models.Model):
    """
    Links a sector to a partnership
    Many-to-many cardinality
    """
    pca = models.ForeignKey(PCA)
    sector = models.ForeignKey(Sector)

    class Meta:
        verbose_name = 'PCA Sector'

    def __unicode__(self):
        return u'{}: {}: {}'.format(
            self.pca.partner.name,
            self.pca.number,
            self.sector.name,
        )

    def changeform_link(self):
        return get_changeform_link(self, link_name='Details')
    changeform_link.allow_tags = True
    changeform_link.short_description = 'View Sector Details'


class PCASectorOutput(models.Model):

    pca_sector = models.ForeignKey(PCASector)
    output = models.ForeignKey(Rrp5Output)

    class Meta:
        verbose_name = 'Output'
        verbose_name_plural = 'Outputs'

    @property
    def pca(self):
        return self.pca_sector.pca


class PCASectorGoal(models.Model):

    pca_sector = models.ForeignKey(PCASector)
    goal = models.ForeignKey(Goal)

    class Meta:
        verbose_name = 'CCC'
        verbose_name_plural = 'CCCs'


class PCASectorActivity(models.Model):

    pca_sector = models.ForeignKey(PCASector)
    activity = models.ForeignKey(Activity)

    class Meta:
        verbose_name = 'Activity'
        verbose_name_plural = 'Activities'


class PCASectorImmediateResult(models.Model):

    pca_sector = models.ForeignKey(PCASector)
    Intermediate_result = models.ForeignKey(IntermediateResult)

    wbs_activities = models.ManyToManyField(WBS)

    class Meta:
        verbose_name = 'Intermediate Result'
        verbose_name_plural = 'Intermediate Results'

    def __unicode__(self):
        return self.Intermediate_result.name


class IndicatorProgress(models.Model):

    pca_sector = models.ForeignKey(PCASector)
    indicator = models.ForeignKey(Indicator)
    programmed = models.PositiveIntegerField()
    current = models.IntegerField(blank=True, null=True, default=0)

    def __unicode__(self):
        return self.indicator.name

    @property
    def pca(self):
        return self.pca_sector.pca

    def shortfall(self):
        return self.programmed - self.current if self.id and self.current else 0
    shortfall.short_description = 'Shortfall'

    def unit(self):
        return self.indicator.unit.type if self.id else ''
    unit.short_description = 'Unit'


class FileType(models.Model):
    name = models.CharField(max_length=64L, unique=True)

    def __unicode__(self):
        return self.name


class PCAFile(models.Model):

    pca = models.ForeignKey(PCA)
    type = models.ForeignKey(FileType)
    file = FilerFileField()

    def __unicode__(self):
        return self.file.file.name

    def download_url(self):
        if self.file:
            return u'<a class="btn btn-primary default" ' \
                   u'href="{}" >Download</a>'.format(self.file.file.url)
        return u''
    download_url.allow_tags = True
    download_url.short_description = 'Download Files'


class SpotCheck(models.Model):

    pca = models.ForeignKey(PCA)
    sector = models.ForeignKey(
        Sector,
        blank=True, null=True
    )
    planned_date = models.DateField(
        blank=True, null=True
    )
    completed_date = models.DateField(
        blank=True, null=True
    )
    amount = models.IntegerField(
        null=True, blank=True,
        default=0
    )
    recommendations = models.TextField(
        blank=True, null=True
    )
    partner_agrees = models.BooleanField(
        default=False
    )


class ResultChain(models.Model):

    partnership = models.ForeignKey(PCA, related_name='results')
    result_type = models.ForeignKey(ResultType)
    result = ChainedForeignKey(
        Result,
        chained_field="result_type",
        chained_model_field="result_type",
        show_all=False,
        auto_choose=False,
    )
    indicator = ChainedForeignKey(
        Indicator,
        chained_field="result",
        chained_model_field="result",
        show_all=False,
        auto_choose=True,
        blank=True, null=True
    )
    governorate = models.ForeignKey(
        Governorate,
        blank=True, null=True
    )
    target = models.PositiveIntegerField(
        blank=True, null=True
    )

    def __unicode__(self):
        return u'{} -> {} -> {}'.format(
            self.result.result_structure.name,
            self.result.sector.name,
            self.result.__unicode__(),
        )


class DistributionPlan(models.Model):

    partnership = models.ForeignKey(PCA)
    item = models.ForeignKey(SupplyItem)
    location = models.ForeignKey(Region)
    quantity = models.PositiveIntegerField()

