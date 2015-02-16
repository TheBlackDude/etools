__author__ = 'jcranwellward'

import json
import datetime
from copy import deepcopy

import requests
import reversion
from django.conf import settings
from django.db import models, transaction
from django.contrib.auth.models import Group
from django.db.models.signals import post_save

from filer.fields.file import FilerFileField
from smart_selects.db_fields import ChainedForeignKey

from EquiTrack.utils import get_changeform_link, AdminURLMixin
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
)
from locations.models import (
    Governorate,
    Locality,
    Location,
    Region,
)
from partners import emails


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
    PCA = u'pca'
    MOU = u'mou'
    SSFA = u'ssfa'
    AWP = u'awp'
    AGREEMENT_TYPES = (
        (PCA, u'Partner Cooperation Agreement'),
        (MOU, u'Memorandum of Understanding'),
        (SSFA, u'Small Scale Funding Agreement'),
        (AWP, u'Annual Work Plan'),
    )

    agreement_type = models.CharField(
        choices=AGREEMENT_TYPES,
        default=PCA,
        blank=True, null=True,
        max_length=255
    )
    result_structure = models.ForeignKey(
        ResultStructure,
        blank=True, null=True,
        help_text=u'Which result structure does this PCA report under?'
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
                  u'Implemented = PCA was completed, '
                  u'Cancelled = PCA was cancelled'
    )
    partner = models.ForeignKey(PartnerOrganization)
    start_date = models.DateField(
        null=True, blank=True,
        help_text=u'The date the PCA will start'
    )
    end_date = models.DateField(
        null=True, blank=True,
        help_text=u'The date the PCA will end'
    )
    initiation_date = models.DateField(
        help_text=u'The date when planning began with the partner'

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
    def sector_id(self):
        sectors = self.pcasector_set.all()
        if sectors:
            return sectors[0].sector.id
        return 0

    def total_unicef_contribution(self):
        cash = self.unicef_cash_budget if self.unicef_cash_budget else 0
        in_kind = self.in_kind_amount_budget if self.in_kind_amount_budget else 0
        return cash + in_kind
    total_unicef_contribution.short_description = 'Total Unicef contribution budget'

    def make_amendment(self, user):
        """
        Creates an amendment (new record) of this PCA copying
        over all values and related objects, marks the existing
        PCA as non current and creates a manual restore point.
        The user who created the amendment is also captured.
        """
        with transaction.atomic(), reversion.create_revision():

            # make original as non current
            original = self
            original.current = False
            original.save()

            # copy base properties to new object
            amendment = deepcopy(original)
            amendment.pk = None
            amendment.amendment = True
            amendment.amended_at = datetime.datetime.now()
            amendment.amendment_number += 1  # increment amendment count
            amendment.original = original
            amendment.save()

            # make manual revision point
            reversion.set_user(user)
            reversion.set_comment("Amendment {} created for PCA: {}".format(
                amendment.amendment_number,
                amendment.number)
            )

        amendment.unicef_managers = original.unicef_managers.all()

        # copy over grants
        for grant in original.pcagrant_set.all():
            PCAGrant.objects.create(
                pca=amendment,
                grant=grant.grant,
                funds=grant.funds
            )

        # copy over sectors
        for pca_sector in original.pcasector_set.all():
            new_sector = PCASector.objects.create(
                pca=amendment,
                sector=pca_sector.sector
            )

            for output in pca_sector.pcasectoroutput_set.all():
                PCASectorOutput.objects.create(
                    pca_sector=new_sector,
                    output=output.output
                )

            for goal in pca_sector.pcasectorgoal_set.all():
                PCASectorGoal.objects.create(
                    pca_sector=new_sector,
                    goal=goal.goal
                )

            for activity in pca_sector.pcasectoractivity_set.all():
                PCASectorActivity.objects.create(
                    pca_sector=pca_sector,
                    activity=activity.activity
                )

            # copy over indicators for sectors and reset programmed number
            for pca_indicator in pca_sector.indicatorprogress_set.all():
                IndicatorProgress.objects.create(
                    pca_sector=new_sector,
                    indicator=pca_indicator.indicator,
                    programmed=0
                )

            # copy over intermediate results and activities
            for pca_ir in pca_sector.pcasectorimmediateresult_set.all():
                new_ir = PCASectorImmediateResult.objects.create(
                    pca_sector=new_sector,
                    Intermediate_result=pca_ir.Intermediate_result
                )
                new_ir.wbs_activities = pca_ir.wbs_activities.all()

    def save(self, **kwargs):
        """
        Calculate total cash on save
        """
        partner_budget = self.partner_contribution_budget \
            if self.partner_contribution_budget else 0
        self.total_cash = partner_budget + self.total_unicef_contribution()

        # populate sectors display string
        if self.pcasector_set.all().count():
            self.sectors = ", ".join(
                [sector.sector.name for sector in self.pcasector_set.all()]
            )

        super(PCA, self).save(**kwargs)

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
    pca = models.ForeignKey(PCA)
    grant = models.ForeignKey(Grant)
    funds = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ['-funds']

    def __unicode__(self):
        return self.grant


class GwPCALocation(models.Model):

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
    )
    location = ChainedForeignKey(
        Location,
        chained_field="locality",
        chained_model_field="locality",
        show_all=False,
        auto_choose=True
    )
    tpm_visit = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'PCA Location'

    def __unicode__(self):
        return u'{} -> {} -> {} -> {}'.format(
            self.governorate.name,
            self.region.name,
            self.locality.name,
            self.location.__unicode__(),
        )

    def view_location(self):
        return get_changeform_link(self)
    view_location.allow_tags = True
    view_location.short_description = 'View Location'


class PCASector(models.Model):

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


class FACE(models.Model):

    REQUESTED = u'requested'
    ACKNOWLEDGED = u'acknowledged'
    PAID = u'paid'
    CANCELLED = u'cancelled'
    FACE_STATUS = (
        (REQUESTED, u"Requested"),
        (ACKNOWLEDGED, u"Acknowledged"),
        (PAID, u"Paid"),
        (CANCELLED, u"Cancelled"),
    )

    ref = models.CharField(max_length=100)
    pca = models.ForeignKey(PCA, related_name='face_refs')
    submited_on = models.DateTimeField(auto_now_add=True)
    amount = models.CharField(max_length=100, default=0)
    status = models.CharField(choices=FACE_STATUS, max_length=100, default=REQUESTED)
    date_paid = models.DateField(verbose_name='Paid On', null=True, blank=True)

    class Meta:
        verbose_name = 'FACE'

    def __unicode__(self):
        return self.ref

    @classmethod
    def notify_face_change(cls, sender, instance, created, **kwargs):
        if instance.PAID and instance.date_paid:
            response = requests.post(
                'https://api.rapidpro.io/api/v1/sms.json',
                headers={
                    'Authorization': 'Token {}'.format(settings.RAPIDPRO_TOKEN),
                    'content-type': 'application/json'
                },
                data=json.dumps(
                    {
                        "phone": [instance.pca.partner.phone_number],
                        "text": "Hi {name}, payment for {pca} FACE Ref# {face} has been processed.".format(
                            name=instance.pca.partner.name,
                            pca=instance.pca.number,
                            face=instance.ref
                        )
                    }
                )

            )
            return response

models.signals.post_save.connect(FACE.notify_face_change, sender=FACE)
