
from partners.models import GovernmentIntervention, GovernmentInterventionResult

from rest_framework import serializers


class GovernmentInterventionResultNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = GovernmentInterventionResult
        fields = ('id', 'intervention', 'result', 'year', 'planned_amount', 'activities', 'unicef_managers', 'sectors',
                  'sections', 'activities_list')

        def validate(self, data):
            """
            Check that the start is before the stop.
            """
            if not data['intervention']:
                raise serializers.ValidationError("There is no partner selected")
            return data


class GovernmentInterventionListSerializer(serializers.ModelSerializer):
    partner_name = serializers.CharField(source='partner.name')
    country_programme_name = serializers.CharField(source='country_programme.name')
    unicef_focal_points = serializers.SerializerMethodField()
    sectors = serializers.SerializerMethodField()

    def get_unicef_focal_points(self, obj):
        unicef_focal_points = []
        for r in obj.results.all():
            unicef_focal_points = list(set([s.id for s in r.unicef_managers.all()] + unicef_focal_points))
        return unicef_focal_points

    def get_sectors(self, obj):
        sectors = []
        for r in obj.results.all():
            sectors = list(set([s.name for s in r.sectors.all()] + sectors))
        return sectors

    class Meta:
        model = GovernmentIntervention
        fields = ("id", "number", "created_at", "partner", "partner_name", "country_programme",
                  "country_programme_name", "unicef_focal_points", "sectors")


class GovernmentInterventionDetailSerializer(serializers.ModelSerializer):
    results = GovernmentInterventionResultNestedSerializer(many=True, read_only=True, required=False)

    class Meta:
        model = GovernmentIntervention
        fields = ("id", "number", "created_at", "partner", "result_structure", "country_programme", "results")


class GovernmentInterventionCreateUpdateSerializer(serializers.ModelSerializer):
    results = GovernmentInterventionResultNestedSerializer(many=True, read_only=True, required=False)

    class Meta:
        model = GovernmentIntervention
        fields = ("id", "number", "created_at", "partner", "result_structure", "country_programme", "results")

        def validate(self, data):
            """
            Check that the start is before the stop.
            """
            if not data['partner']:
                raise serializers.ValidationError("There is no partner selected")
            if not data['country_programme']:
                raise serializers.ValidationError("There is no country programme selected")
            return data


class GovernmentInterventionExportSerializer(serializers.ModelSerializer):

    class Meta:
        model = GovernmentIntervention
        fields = '__all__'