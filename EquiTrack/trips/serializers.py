__author__ = 'jcranwellward'

from django.contrib.sites.models import Site

from rest_framework import serializers

from .models import Trip, TravelRoutes, TripFunds


class TravelRoutesSerializer(serializers.ModelSerializer):

    class Meta:
        model = TravelRoutes
        fields = (
            'origin',
            'destination',
            'depart',
            'arrive',
            'remarks'
        )

class TripFundsSerializer(serializers.ModelSerializer):
    wbs = serializers.CharField(source='wbs.name')
    grant = serializers.CharField(source='grant.name')

    class Meta:
        model = TripFunds
        fields = (
            'wbs',
            'grant',
            'amount'
        )


class TripSerializer(serializers.ModelSerializer):

    traveller = serializers.CharField(source='owner')
    traveller_id = serializers.IntegerField(source='owner.id')
    supervisor_name = serializers.CharField(source='supervisor')
    section = serializers.CharField(source='section.name')
    travel_type = serializers.CharField()
    # related_to_pca = serializers.CharField(source='no_pca')
    url = serializers.CharField(source='get_admin_url')

    #It is redundant to specify `source='travel_assistant'`
    # on field 'CharField' in serializer 'TripSerializer', because it is the same as the field name.
    travel_assistant = serializers.CharField()
    security_clearance_required = serializers.CharField()
    ta_required = serializers.CharField()
    budget_owner = serializers.CharField()
    staff_responsible_ta = serializers.CharField(source='programme_assistant')
    international_travel = serializers.CharField()
    representative = serializers.CharField()
    human_resources = serializers.CharField()
    approved_by_human_resources = serializers.CharField()
    vision_approver = serializers.CharField()
    partners = serializers.CharField()
    travel_routes = serializers.SerializerMethodField('get_TravelRoutes')
    trip_funds = serializers.SerializerMethodField('get_TripFunds')
    office =  serializers.CharField(source='office.name')

    def get_TravelRoutes(self, trip):
        return TravelRoutesSerializer(
            trip.travelroutes_set.all(),
            many=True
        ).data


    def get_TripFunds(self, trip):
        return TripFundsSerializer(
            trip.tripfunds_set.all(),
            many=True
        ).data

    def transform_traveller(self, obj, value):
        return obj.owner.get_full_name()

    def transform_supervisor_name(self, obj, value):
        return obj.supervisor.get_full_name()

    def get_partners(self, obj, value):
        return ', '.join([
            partner.name for partner in obj.partners.all()
        ])

    def transform_pcas(self, obj, value):
        return ', '.join([
            pca.__unicode__() for pca in obj.pcas.all()
        ])

    def transform_url(self, obj, value):
        return 'http://{}{}'.format(
            Site.objects.get_current(),
            obj.get_admin_url()
        )

    class Meta:
        model = Trip
        fields = (
            'id',
            'url',
            'traveller',
            'traveller_id',
            'supervisor',
            'supervisor_name',
            'travel_assistant',
            'section',
            'purpose_of_travel',
            'office',
            'travel_type',
            'from_date',
            'to_date',
            # 'related_to_pca',
            'partners',
            'status',
            'security_clearance_required',
            'ta_required',
            'budget_owner',
            'staff_responsible_ta',
            'international_travel',
            'representative',
            'human_resources',

            'approved_by_supervisor',
            'date_supervisor_approved',
            'approved_by_budget_owner',
            'date_budget_owner_approved',
            'approved_by_human_resources',
            'date_human_resources_approved',
            'representative_approval',
            'date_representative_approved',
            'approved_date',
            'transport_booked',
            'security_granted',
            'ta_drafted',
            'ta_drafted_date',
            'ta_reference',
            'vision_approver',
            'partners',
            'pcas',
            'travel_routes',
            'trip_funds'



        )





