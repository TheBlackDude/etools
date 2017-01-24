from __future__ import unicode_literals

from rest_framework import serializers

from t2f.models import Travel
from t2f.serializers import TravelListSerializer


class TravelListExportSerializer(TravelListSerializer):
    traveler = serializers.CharField(source='traveler.get_full_name')
    section = serializers.CharField(source='section.name')
    office = serializers.CharField(source='office.name')

    class Meta:
        model = Travel
        fields = ('id', 'reference_number', 'traveler', 'purpose', 'status', 'section', 'office', 'start_date',
                  'end_date')


class FinanceExportSerializer(serializers.Serializer):
    reference_number = serializers.CharField()
    traveller = serializers.CharField(source='traveller.get_full_name')
    office = serializers.CharField(source='office.name')
    section = serializers.CharField(source='section.name')
    status = serializers.CharField()
    supervisor = serializers.CharField(source='supervisor.get_full_name')
    start_date = serializers.DateTimeField()
    end_date = serializers.DateTimeField()
    purpose_of_travel = serializers.CharField(source='purpose')
    mode_of_travel = serializers.SerializerMethodField()
    international_travel = serializers.BooleanField()
    require_ta = serializers.BooleanField()
    dsa_total = serializers.DecimalField(source='cost_summary.dsa_total', max_digits=20, decimal_places=10)
    expense_total = serializers.DecimalField(source='cost_summary.expenses_total', max_digits=20, decimal_places=10)
    deductions_total = serializers.DecimalField(source='cost_summary.deductions_total', max_digits=20, decimal_places=10)

    class Meta:
        fields = ('reference_number', 'traveller', 'office', 'section', 'status', 'supervisor', 'start_date',
                  'end_date', 'purpose_of_travel', 'mode_of_travel', 'international_travel', 'require_ta', 'dsa_total',
                  'expense_total', 'deductions_total')

    def get_mode_of_travel(self, obj):
        return ', '.join(obj.mode_of_travel)


class TravelAdminExportSerializer(serializers.Serializer):
    reference_number = serializers.CharField(source='travel.reference_number')
    traveller = serializers.CharField(source='travel.traveler.get_full_name')
    office = serializers.CharField(source='travel.office.name')
    section = serializers.CharField(source='travel.section.name')
    status = serializers.CharField(source='travel.status')
    origin = serializers.CharField()
    destination = serializers.CharField()
    departure_time = serializers.DateTimeField(source='departure_date')
    arrival_time = serializers.DateTimeField(source='arrival_date')
    dsa_area = serializers.CharField(source='dsa_region.area_code')
    overnight_travel = serializers.BooleanField()
    mode_of_travel = serializers.CharField()
    airline = serializers.CharField(source='airlines.0.name')

    class Meta:
        fields = ('reference_number', 'traveller', 'office', 'section', 'status', 'origin', 'destination',
                  'departure_time', 'arrival_time', 'dsa_area', 'overnight_travel', 'mode_of_travel', 'airline')



class InvoiceExportSerializer(serializers.Serializer):
    reference_number = serializers.CharField()
    ta_number = serializers.CharField()
    vendor_number = serializers.CharField()
    currency = serializers.CharField()
    amount = serializers.CharField()
    status = serializers.CharField()
    message = serializers.CharField()
    vision_fi_doc = serializers.CharField()
    wbs = serializers.CharField()
    grant = serializers.CharField()
    fund = serializers.CharField()

    class Meta:
        fields = ('reference_number', 'ta_number', 'vendor_number', 'currency', 'amount', 'status', 'message',
                  'vision_fi_doc', 'wbs', 'grant', 'fund')
