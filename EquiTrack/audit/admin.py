from django.contrib import admin
from ordered_model.admin import OrderedModelAdmin

from . import models


@admin.register(models.AuditPermission)
class AuditPermissionAdmin(admin.ModelAdmin):
    list_display = ['target', 'user_type', 'permission_type', 'permission', 'instance_status']
    list_filter = ['user_type', 'permission_type', 'permission', 'instance_status']
    search_fields = ['target']


class AuditOrganizationStaffMemberInlineAdmin(admin.StackedInline):
    model = models.AuditOrganizationStaffMember
    extra = 1


@admin.register(models.AuditOrganization)
class AuditOrganizationAdmin(admin.ModelAdmin):
    list_display = [
        'vendor_number', 'name', 'email', 'phone_number', 'blocked', 'hidden',
        'country',
    ]
    list_filter = ['blocked', 'hidden', 'country', ]
    search_fields = ['vendor_number', 'name', ]
    inlines = [
        AuditOrganizationStaffMemberInlineAdmin,
    ]


@admin.register(models.PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_number', 'audit_organization', 'contract_start_date',
        'contract_end_date',
    ]
    list_filter = [
        'audit_organization', 'contract_start_date', 'contract_end_date',
    ]
    search_fields = ['order_number', 'audit_organization__name', ]


@admin.register(models.Engagement)
class EngagementAdmin(admin.ModelAdmin):
    list_display = [
        '__str__', 'status', 'partner', 'date_of_field_visit',
        'type', 'start_date', 'end_date',
    ]
    list_filter = [
        'status', 'start_date', 'end_date', 'status', 'type',
    ]
    readonly_fields = ('status', )
    search_fields = ['partner__name', 'audit_organization__name', ]


@admin.register(models.RiskCategory)
class RiskCategoryAdmin(OrderedModelAdmin):
    list_display = [
        '__str__', 'type', 'code', 'header', 'parent', 'move_up_down_links',
    ]
    list_filter = ['type', ]
    search_fields = ['code', 'header', ]
    readonly_fields = ['code', ]


@admin.register(models.RiskBluePrint)
class RiskBluePrintAdmin(OrderedModelAdmin):
    list_display = [
        '__str__', 'weight', 'is_key', 'description', 'category', 'move_up_down_links',
    ]
    list_filter = ['is_key', ]


@admin.register(models.Risk)
class RiskAdmin(admin.ModelAdmin):
    list_display = [
        '__str__', 'value', 'blueprint', 'extra',
    ]
    list_filter = ['value', ]


@admin.register(models.SpotCheck)
class SpotCheckAdmin(EngagementAdmin):
    pass


@admin.register(models.MicroAssessment)
class MicroAssessmentAdmin(EngagementAdmin):
    pass


@admin.register(models.Audit)
class AuditAdmin(EngagementAdmin):
    pass


@admin.register(models.Finding)
class FindingAdmin(admin.ModelAdmin):
    list_display = [
        '__str__', 'priority', 'deadline_of_action',
        'category_of_observation',
    ]
    list_filter = [
        'category_of_observation', 'priority', 'deadline_of_action',
    ]


@admin.register(models.FinancialFinding)
class FinancialFindingAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'id', 'audit', 'description', 'amount', 'local_amount',
    ]
    search_fields = ['id', 'title', ]
