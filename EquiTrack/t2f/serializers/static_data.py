from __future__ import unicode_literals

from django.contrib.auth import get_user_model
from rest_framework import serializers

from locations.models import Location
from partners.models import PartnerOrganization, Intervention, InterventionResultLink, GovernmentIntervention, \
    GovernmentInterventionResult
from reports.models import Result
from users.models import Office, Section


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='get_full_name')

    class Meta:
        model = get_user_model()
        fields = ('id', 'full_name')


class OfficeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Office
        fields = ('id', 'name')


class SectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Section
        fields = ('id', 'name')


class PartnerOrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartnerOrganization
        fields = ('id', 'name')


class PartnershipSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='title')
    partner = serializers.PrimaryKeyRelatedField(source='agreement.partner', read_only=True)
    results = serializers.SerializerMethodField()

    class Meta:
        model = Intervention
        fields = ('id', 'name', 'partner', 'results')

    def get_results(self, obj):
        return InterventionResultLink.objects.filter(intervention=obj).values_list('cp_output_id', flat=True)


class GovernmentPartnershipSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='reference_number')
    partner = serializers.PrimaryKeyRelatedField(read_only=True)
    results = serializers.SerializerMethodField()

    class Meta:
        model = GovernmentIntervention
        fields = ('id', 'name', 'partner', 'results')

    def get_results(self, obj):
        return GovernmentInterventionResult.objects.filter(intervention=obj).values_list('result_id', flat=True)


class ResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = Result
        fields = ('id', 'name')


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ('id', 'name')


class StaticDataSerializer(serializers.Serializer):
    partners = PartnerOrganizationSerializer(many=True)
    partnerships = PartnershipSerializer(many=True)
    government_partnerships = GovernmentPartnershipSerializer(many=True)
    results = ResultSerializer(many=True)
    locations = LocationSerializer(many=True)
    travel_types = serializers.ListField(child=serializers.CharField())
    travel_modes = serializers.ListField(child=serializers.CharField())
    action_point_statuses = serializers.ListField(child=serializers.CharField())
