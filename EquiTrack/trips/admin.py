__author__ = 'jcranwellward'

from django.db.models import Q
from django.contrib import admin
from django.contrib import messages
from django.contrib.sites.models import Site
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.contenttypes.generic import GenericTabularInline

from reversion import VersionAdmin
from import_export.admin import ExportMixin
from generic_links.admin import GenericLinkStackedInline
from messages_extends import constants as constants_messages
from users.models import UserProfile

from EquiTrack.forms import AutoSizeTextForm
from locations.models import LinkedLocation
from .models import (
    Trip,
    Office,
    TripFunds,
    ActionPoint,
    TravelRoutes,
    FileAttachment,
    TripLocation,

)
from .forms import (
    TripForm,
    TravelRoutesForm,
    RequiredInlineFormSet,
)

from .exports import TripResource, ActionPointResource

User = get_user_model()


class TravelRoutesInlineAdmin(admin.TabularInline):
    model = TravelRoutes
    form = TravelRoutesForm
    suit_classes = u'suit-tab suit-tab-planning'
    verbose_name = u'Travel Itinerary'
    extra = 5


class TripFundsInlineAdmin(admin.TabularInline):
    model = TripFunds
    suit_classes = u'suit-tab suit-tab-planning'
    extra = 3
    max_num = 3


class ActionPointInlineAdmin(admin.StackedInline):
    model = ActionPoint
    form = AutoSizeTextForm
    suit_classes = u'suit-tab suit-tab-reporting'
    filter_horizontal = (u'persons_responsible',)
    extra = 1
    fields = (
        (u'description', u'due_date',),
        u'person_responsible',
        (u'actions_taken',),
        (u'completed_date', u'status'),
    )


class SitesVisitedInlineAdmin(admin.TabularInline):
    model = TripLocation
    formset = RequiredInlineFormSet
    suit_classes = u'suit-tab suit-tab-planning'
    verbose_name = u'Sites to visit'
    extra = 1


class FileAttachmentInlineAdmin(GenericTabularInline):
    model = FileAttachment
    suit_classes = u'suit-tab suit-tab-attachments'
    fields = (u'type', u'report')


class LinksInlineAdmin(GenericLinkStackedInline):
    suit_classes = u'suit-tab suit-tab-attachments'
    extra = 1


class TripReportFilter(admin.SimpleListFilter):

    title = 'Report'
    parameter_name = 'report'

    def lookups(self, request, model_admin):

        return [
            ('Yes', 'Completed'),
            ('No', 'Not-Completed'),
        ]

    def queryset(self, request, queryset):

        if self.value():
            is_null = Q(main_observations='')
            return queryset.filter(is_null if self.value() == 'No' else ~is_null)
        return queryset


class TripReportAdmin(ExportMixin, VersionAdmin):
    resource_class = TripResource
    save_as = True  # TODO: There is a bug using this
    form = TripForm
    inlines = (
        TravelRoutesInlineAdmin,
        TripFundsInlineAdmin,
        SitesVisitedInlineAdmin,
        ActionPointInlineAdmin,
        FileAttachmentInlineAdmin,
        LinksInlineAdmin,
    )
    ordering = (u'-created_date',)
    date_hierarchy = u'from_date'
    search_fields = (
        u'owner',
        u'section',
        u'office',
        u'purpose_of_travel',
    )
    list_display = (
        u'reference',
        u'created_date',
        u'purpose_of_travel',
        u'owner',
        u'section',
        u'office',
        u'from_date',
        u'to_date',
        u'supervisor',
        u'status',
        u'approved_date',
        u'outstanding_actions',
    )
    list_filter = (
        u'owner',
        u'section',
        u'office',
        u'from_date',
        u'to_date',
        u'travel_type',
        u'international_travel',
        u'supervisor',
        u'budget_owner',
        u'status',
        u'approved_date',
        TripReportFilter,
    )
    filter_vertical = (
        u'pcas',
        u'partners',
    )
    readonly_fields = (
        u'reference',
    )
    fieldsets = (
        (u'Traveler', {
            u'classes': (u'suit-tab suit-tab-planning',),
            u'fields':
                ((u'status', u'cancelled_reason'),
                 u'owner',
                 u'supervisor',
                 (u'section', u'office',),
                 (u'purpose_of_travel',),
                 (u'from_date', u'to_date',),
                 (u'travel_type', u'travel_assistant',),
                 u'security_clearance_required',
                 u'ta_required',
                 u'budget_owner',
                 u'programme_assistant',
                 (u'international_travel', u'representative',),
                 u'approved_by_human_resources',)
        }),
        (u'PCA Details', {
            u'classes': (u'suit-tab suit-tab-planning',),
            u'fields':
                (u'pcas',
                 u'partners',),
        }),
        (u'Approval', {
            u'classes': (u'suit-tab suit-tab-planning',),
            u'fields':
                ((u'approved_by_supervisor', u'date_supervisor_approved',),
                 (u'approved_by_budget_owner', u'date_budget_owner_approved',),
                 (u'date_human_resources_approved', u'human_resources'),
                 (u'representative_approval', u'date_representative_approved',),
                 u'approved_date',),
        }),
        (u'Travel/Admin', {
            u'classes': (u'suit-tab suit-tab-planning',),
            u'fields':
                (u'transport_booked',
                 u'security_granted',
                 u'ta_drafted',
                 u'ta_reference',
                 u'ta_drafted_date',
                 u'vision_approver',),
        }),

        (u'Report', {
            u'classes': (u'suit-tab suit-tab-reporting', u'full-width',),
            u'fields': (
                u'main_observations',),
        }),

        (u'Travel Closure', {
            u'classes': (u'suit-tab suit-tab-reporting',),
            u'fields': (
                u'ta_trip_took_place_as_planned',
                u'ta_trip_repay_travel_allowance',
                u'ta_trip_final_claim'),
        }),
    )
    suit_form_tabs = (
        (u'planning', u'Planning'),
        (u'reporting', u'Reporting'),
        (u'attachments', u'Attachments')
    )

    def save_formset(self, request, form, formset, change):
        """
        Override here to check if the itinerary has changed
        """
        for form in formset.forms:
            if form.has_changed():  #TODO: Test this
                if type(form.instance) is TravelRoutes and form.instance.trip.status == Trip.APPROVED:
                    trip = Trip.objects.get(pk=form.instance.trip.pk)
                    trip.status = Trip.SUBMITTED
                    trip.approved_by_supervisor = False
                    trip.date_supervisor_approved = None
                    trip.approved_by_budget_owner = False
                    trip.date_budget_owner_approved = None
                    trip.approved_by_human_resources = None
                    trip.representative_approval = None
                    trip.date_representative_approved = None
                    trip.approved_date = None
                    trip.approved_email_sent = False
                    trip.save()

        formset.save()

    def get_readonly_fields(self, request, trip=None):
        """
        Only let certain users perform approvals
        """
        fields = [
            u'status',
            u'approved_by_supervisor',
            u'date_supervisor_approved',
            u'approved_by_budget_owner',
            u'date_budget_owner_approved',
            u'human_resources',
            u'approved_by_human_resources',
            u'date_human_resources_approved',
            u'representative_approval',
            u'date_representative_approved',
            u'approved_date'
        ]

        if trip and trip.status == Trip.PLANNED and request.user in [
            trip.owner,
            trip.travel_assistant,
            trip.supervisor
        ]:
            fields.remove(u'status')

        if trip and trip.status == Trip.APPROVED and request.user in [
            trip.owner,
            trip.travel_assistant,
            trip.programme_assistant
        ]:
            fields.remove(u'status')

        if trip and request.user == trip.supervisor:
            fields.remove(u'approved_by_supervisor')
            fields.remove(u'date_supervisor_approved')

        if trip and request.user == trip.budget_owner:
            fields.remove(u'approved_by_budget_owner')
            fields.remove(u'date_budget_owner_approved')

        hr_group, created = Group.objects.get_or_create(
            name=u'Human Resources'
        )
        if trip and hr_group in request.user.groups.all():
            fields.remove(u'human_resources')
            fields.remove(u'approved_by_human_resources')
            fields.remove(u'date_human_resources_approved')

        rep_group, created = Group.objects.get_or_create(
            name=u'Representative Office'
        )
        if trip and rep_group in request.user.groups.all():
            fields.remove(u'representative_approval')
            fields.remove(u'date_representative_approved')

        if trip and request.user.is_superuser:
            return []

        return fields

    def get_form(self, request, obj=None, **kwargs):
        form = super(TripReportAdmin, self).get_form(request, obj, **kwargs)
        form.request = request
        try:
            user_profile = request.user.get_profile()
            form.base_fields['owner'].initial = request.user
            form.base_fields['office'].initial = user_profile.office
            form.base_fields['section'].initial = user_profile.section
        except UserProfile.DoesNotExist:
            form.base_fields['owner'].initial = request.user
        return form

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):

        if db_field.name == u'representative':
            rep_group = Group.objects.get(name=u'Representative Office')
            kwargs['queryset'] = rep_group.user_set.all()

        return super(TripReportAdmin, self).formfield_for_foreignkey(
            db_field, request, **kwargs
        )


class ActionPointsAdmin(ExportMixin, admin.ModelAdmin):
    resource_class = ActionPointResource
    exclude = [u'persons_responsible']
    date_hierarchy = u'due_date'
    list_display = (
        u'trip',
        u'description',
        u'due_date',
        u'person_responsible',
        u'originally_responsible',
        u'actions_taken',
        u'comments',
        u'status'
    )
    list_filter = (
        u'trip__owner',
        u'person_responsible',
        u'status',
    )
    search_fields = (
        u'trip__name',
        u'description',
        u'actions_taken',
    )

    def trip(self, obj):
        return unicode(obj.trip)

    def originally_responsible(self, obj):
        return ', '.join(
            [
                user.get_full_name()
                for user in
                obj.persons_responsible.all()
            ]
        )

    def get_readonly_fields(self, request, obj=None):

        readonly_fields = [
            u'trip',
            u'description',
            u'due_date',
            u'person_responsible',
            u'persons_responsible',
            u'comments',
            u'status',
        ]

        if obj and obj.person_responsible == request.user:
            readonly_fields.remove(u'comments')
            readonly_fields.remove(u'status')

        return readonly_fields


admin.site.register(Office)
admin.site.register(Trip, TripReportAdmin)
admin.site.register(ActionPoint, ActionPointsAdmin)