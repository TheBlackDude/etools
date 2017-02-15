import json
from operator import xor

from django.core.exceptions import ValidationError
from django.db import transaction
from rest_framework import serializers

from reports.serializers.v1 import SectorLightSerializer, ResultLightSerializer, RAMIndicatorLightSerializer
from reports.serializers.v2 import LowerResultSerializer, LowerResultCUSerializer
from locations.models import Location

from partners.models import (
    PCA,
    InterventionBudget,
    SupplyPlan,
    DistributionPlan,
    InterventionPlannedVisits,
    Intervention,
    InterventionAmendment,
    InterventionAttachment,
    PartnerOrganization,
    PartnerType,
    Agreement,
    PartnerStaffMember,
    InterventionSectorLocationLink,
    InterventionResultLink
)
from reports.models import LowerResult
from locations.serializers import LocationLightSerializer

from partners.serializers.v1 import PCASectorSerializer, DistributionPlanSerializer


class InterventionBudgetNestedSerializer(serializers.ModelSerializer):

    class Meta:
        model = InterventionBudget
        fields = (
            "id",
            "partner_contribution",
            "unicef_cash",
            "in_kind_amount",
            "partner_contribution_local",
            "unicef_cash_local",
            "in_kind_amount_local",
            "year",
            "total",
        )


class InterventionBudgetCUSerializer(serializers.ModelSerializer):
    total = serializers.DecimalField(max_digits=20, decimal_places=2, read_only=True)
    partner_contribution = serializers.DecimalField(max_digits=20, decimal_places=2)
    unicef_cash = serializers.DecimalField(max_digits=20, decimal_places=2)
    in_kind_amount = serializers.DecimalField(max_digits=20, decimal_places=2)
    partner_contribution_local = serializers.DecimalField(max_digits=20, decimal_places=2)
    unicef_cash_local = serializers.DecimalField(max_digits=20, decimal_places=2)
    in_kind_amount_local = serializers.DecimalField(max_digits=20, decimal_places=2)

    class Meta:
        model = InterventionBudget
        fields = (
            "id",
            "intervention",
            "partner_contribution",
            "unicef_cash",
            "in_kind_amount",
            "partner_contribution_local",
            "unicef_cash_local",
            "in_kind_amount_local",
            "year",
            "total",
        )
        #read_only_fields = [u'total']

    def validate(self, data):
        errors = {}
        try:
            data = super(InterventionBudgetCUSerializer, self).validate(data)
        except ValidationError as e:
            errors.update(e)

        intervention = data.get('intervention', None)

        year = data.get("year", "")
        # To avoid any confusion.. budget year will always be required
        if not year:
            errors.update(year="Budget year is required")

        if errors:
            raise serializers.ValidationError(errors)

        return data


class SupplyPlanCreateUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = SupplyPlan
        fields = "__all__"


class SupplyPlanNestedSerializer(serializers.ModelSerializer):

    class Meta:
        model = SupplyPlan
        fields = (
            'id',
            "item",
            "quantity",
        )


class DistributionPlanCreateUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = DistributionPlan
        fields = "__all__"


class DistributionPlanNestedSerializer(serializers.ModelSerializer):

    class Meta:
        model = DistributionPlan
        fields = "__all__"


class InterventionAmendmentCUSerializer(serializers.ModelSerializer):

    class Meta:
        model = InterventionAmendment
        fields = "__all__"


class PlannedVisitsCUSerializer(serializers.ModelSerializer):

    class Meta:
        model = InterventionPlannedVisits
        fields = "__all__"


class PlannedVisitsNestedSerializer(serializers.ModelSerializer):

    class Meta:
        model = InterventionPlannedVisits
        fields = (
            "id",
            "year",
            "programmatic",
            "spot_checks",
            "audit",
        )


class InterventionListSerializer(serializers.ModelSerializer):

    partner_name = serializers.CharField(source='agreement.partner.name')

    unicef_budget = serializers.IntegerField(source='total_unicef_cash')
    cso_contribution = serializers.IntegerField(source='total_partner_contribution')
    sectors = serializers.SerializerMethodField()
    cp_outputs = serializers.SerializerMethodField()

    def get_cp_outputs(self, obj):
        return [rl.cp_output.id for rl in obj.result_links.all()]

    def get_sectors(self, obj):
        return [l.sector.name for l in obj.sector_locations.all()]

    class Meta:
        model = Intervention
        fields = (
            'id', 'number', 'hrp', 'document_type', 'partner_name', 'status', 'title', 'start', 'end',
            'unicef_budget', 'cso_contribution',
            'sectors', 'cp_outputs', 'unicef_focal_points',
            'offices'
        )

class InterventionLocationSectorNestedSerializer(serializers.ModelSerializer):
    locations = LocationLightSerializer(many=True)
    sector = SectorLightSerializer()
    class Meta:
        model = InterventionSectorLocationLink
        fields = (
            'id', 'sector', 'locations'
        )

class InterventionSectorLocationCUSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterventionSectorLocationLink
        fields = (
            'id', 'intervention', 'sector', 'locations'
        )

class InterventionAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterventionAttachment
        fields = (
            'id', 'intervention', 'type', 'attachment'
        )

class InterventionResultNestedSerializer(serializers.ModelSerializer):
    #cp_output = ResultLightSerializer()
    #ram_indicators = RAMIndicatorLightSerializer(many=True, read_only=True)
    ll_results = LowerResultSerializer(many=True, read_only=True)

    class Meta:
        model = InterventionResultLink
        fields = (
            'id', 'intervention', 'cp_output', 'ram_indicators', 'll_results'
        )

class InterventionResultCUSerializer(serializers.ModelSerializer):

    lower_results = LowerResultSerializer(many=True, read_only=True)

    class Meta:
        model = InterventionResultLink
        fields = "__all__"

    def update_ll_results(self, instance, ll_results):
        for result in ll_results:
            result['result_link'] = instance.pk
            applied_indicators = {'applied_indicators': result.pop('applied_indicators', [])}
            instance_id = result.get('id', None)
            if instance_id:
                try:
                    ll_result_instance = LowerResult.objects.get(pk=instance_id)
                except LowerResult.DoesNotExist as e:
                    raise ValidationError('lower_result has an id but cannot be found in the db')

                ll_result_serializer = LowerResultCUSerializer(
                    instance=ll_result_instance,
                    data=result,
                    context=applied_indicators,
                    partial=True
                )

            else:
                ll_result_serializer = LowerResultCUSerializer(data=result, context=applied_indicators)

            if ll_result_serializer.is_valid(raise_exception=True):
                ll_result_serializer.save()



    @transaction.atomic
    def create(self, validated_data):
        ll_results = self.context.pop('ll_results', [])

        print ('INTERVENTION RESULT CU SERIALIZER CREATE __ IS THIS WORKING?')
        instance = super(InterventionResultCUSerializer, self).create(validated_data)
        print instance.pk
        self.update_ll_results(instance, ll_results)

        return instance

    @transaction.atomic
    def update(self, instance, validated_data):
        ll_results = self.context.pop('ll_results', [])

        self.update_ll_results(instance, ll_results)

        print validated_data
        return super(InterventionResultCUSerializer, self).update(instance, validated_data)


class InterventionCreateUpdateSerializer(serializers.ModelSerializer):

    planned_budget = InterventionBudgetNestedSerializer(many=True, read_only=True)
    partner = serializers.CharField(source='agreement.partner.name', read_only=True)

    supplies = SupplyPlanCreateUpdateSerializer(many=True, read_only=True, required=False)
    distributions = DistributionPlanCreateUpdateSerializer(many=True, read_only=True, required=False)
    amendments = InterventionAmendmentCUSerializer(many=True, read_only=True, required=False)
    planned_visits = PlannedVisitsNestedSerializer(many=True, read_only=True, required=False)
    attachments = InterventionAttachmentSerializer(many=True, read_only=True, required=False)
    sector_locations = InterventionSectorLocationCUSerializer(many=True, read_only=True, required=False)
    result_links = InterventionResultCUSerializer(many=True, read_only=True, required=False)

    class Meta:
        model = Intervention
        fields = "__all__"

    @transaction.atomic
    def update(self, instance, validated_data):
        updated = super(InterventionCreateUpdateSerializer, self).update(instance, validated_data)
        return updated


class InterventionDetailSerializer(serializers.ModelSerializer):
    planned_budget = InterventionBudgetNestedSerializer(many=True, read_only=True)
    partner = serializers.CharField(source='agreement.partner.name')
    supplies = SupplyPlanNestedSerializer(many=True, read_only=True, required=False)
    distributions = DistributionPlanNestedSerializer(many=True, read_only=True, required=False)
    amendments = InterventionAmendmentCUSerializer(many=True, read_only=True, required=False)
    planned_visits = PlannedVisitsNestedSerializer(many=True, read_only=True, required=False)
    sector_locations = InterventionLocationSectorNestedSerializer(many=True, read_only=True, required=False)
    attachments = InterventionAttachmentSerializer(many=True, read_only=True, required=False)
    result_links = InterventionResultNestedSerializer(many=True, read_only=True, required=False)
    class Meta:
        model = Intervention
        fields = (
            "id", "partner", "agreement", "document_type", "hrp", "number",
            "title", "status", "start", "end", "submission_date_prc", "review_date_prc",
            "submission_date", "prc_review_document", "signed_by_unicef_date", "signed_by_partner_date",
            "unicef_signatory", "unicef_focal_points", "partner_focal_points", "partner_authorized_officer_signatory",
            "offices", "fr_numbers", "planned_visits", "population_focus", "sector_locations",
            "created", "modified", "planned_budget", "result_links",
            "amendments", "planned_visits", "attachments", "supplies", "distributions"
        )

class InterventionExportSerializer(serializers.ModelSerializer):

    # TODO CP Outputs, RAM Indicators, Fund Commitment(s), Supply Plan, Distribution Plan, URL

    partner_name = serializers.CharField(source='agreement.partner.name')
    agreement_name = serializers.CharField(source='agreement.agreement_number')
    offices = serializers.SerializerMethodField()
    sectors = serializers.SerializerMethodField()
    locations = serializers.SerializerMethodField()
    planned_budget_local = serializers.IntegerField(source='total_budget_local')
    unicef_budget = serializers.IntegerField(source='total_unicef_cash')
    cso_contribution = serializers.IntegerField(source='total_partner_contribution')
    partner_contribution_local = serializers.IntegerField(source='total_partner_contribution_local')
    # unicef_cash_local = serializers.IntegerField(source='total_unicef_cash_local')
    unicef_signatory = serializers.SerializerMethodField()
    hrp_name = serializers.CharField(source='hrp.name')
    partner_focal_points = serializers.SerializerMethodField()
    supply_plans = serializers.SerializerMethodField()
    distribution_plans = serializers.SerializerMethodField()
    unicef_focal_points = serializers.SerializerMethodField()
    cp_outputs = serializers.SerializerMethodField()
    ram_indicators = serializers.SerializerMethodField()
    planned_visits = serializers.SerializerMethodField()
    spot_checks = serializers.SerializerMethodField()
    audit = serializers.SerializerMethodField()

    class Meta:
        model = Intervention
        fields = (
            "status", "partner_name", "agreement_name", "document_type", "number", "title",
            "start", "end", "offices", "sectors", "locations", "unicef_focal_points",
            "partner_focal_points", "population_focus", "hrp_name", "cp_outputs", "ram_indicators", "fr_numbers",
            "planned_budget_local", "unicef_budget", "cso_contribution",
            "partner_contribution_local", "planned_visits", "spot_checks", "audit", "submission_date",
            "submission_date_prc", "review_date_prc", "unicef_signatory", "signed_by_unicef_date",
            "signed_by_partner_date", "supply_plans", "distribution_plans",
        )

    def get_unicef_signatory(self, obj):
        return obj.unicef_signatory.get_full_name() if obj.unicef_signatory else ''

    def get_offices(self, obj):
        return ', '.join([o.name for o in obj.offices.all()])

    def get_sectors(self, obj):
        return ', '.join([l.sector.name for l in obj.sector_locations.all()])

    def get_locations(self, obj):
        ll = Location.objects.filter(intervention_sector_locations__intervention=obj.id).order_by('name')
        return ', '.join([l.name for l in ll.all()])

    def get_partner_authorized_officer_signatory(self, obj):
        return obj.partner_authorized_officer_signatory.get_full_name() if obj.partner_authorized_officer_signatory else ''

    def get_partner_focal_points(self, obj):
        return ', '.join([pf.get_full_name() for pf in obj.partner_focal_points.all()])

    def get_unicef_focal_points(self, obj):
        return ', '.join([pf.get_full_name() for pf in obj.unicef_focal_points.all()])

    def get_cp_outputs(self, obj):
        return ', '.join([rs.cp_output.name for rs in obj.result_links.all()])

    def get_ram_indicators(self, obj):
        ram_indicators = []
        for rs in obj.result_links.all():
            if rs.ram_indicators:
                for ram in rs.ram_indicators.all():
                    ram_indicators.append("{}, ".format(ram.name))

    def get_planned_visits(self, obj):
        return ', '.join(['{} ({})'.format(pv.programmatic, pv.year) for pv in obj.planned_visits.all()])

    def get_spot_checks(self, obj):
        return ', '.join(['{} ({})'.format(pv.spot_checks, pv.year) for pv in obj.planned_visits.all()])

    def get_audit(self, obj):
        return ', '.join(['{} ({})'.format(pv.audit, pv.year) for pv in obj.planned_visits.all()])

    def get_supply_plans(self, obj):
        return ', '.join(['"{}" ({})'.format(s.item.name, s.quantity) for s in obj.supplies.all()])

    def get_distribution_plans(self, obj):
        return ', '.join(['"{}"/{} ({})'.format(d.item.name, d.quantity, d.site) for d in obj.distributions.all()])
