from __future__ import unicode_literals

from django.conf import settings

from rest_framework import generics, status
from rest_framework.response import Response

from locations.models import Location
from partners.models import PartnerOrganization, Intervention
from publics.models import TravelAgent
from reports.models import Result

from t2f.models import TravelType, ModeOfTravel, ActionPoint
from t2f.serializers.static_data import StaticDataSerializer
from t2f.permission_matrix import PERMISSION_MATRIX
from t2f.views import get_filtered_users
from users.models import UserProfile


class StaticDataView(generics.GenericAPIView):
    serializer_class = StaticDataSerializer

    def get(self, request):
        data = {'partners': PartnerOrganization.objects.all(),
                'partnerships': Intervention.objects.all(),
                'results': Result.objects.all(),
                'locations': Location.objects.all(),
                'travel_types': [c[0] for c in TravelType.CHOICES],
                'travel_modes': [c[0] for c in ModeOfTravel.CHOICES],
                'action_point_statuses': [c[0] for c in ActionPoint.STATUS]}

        serializer = self.get_serializer(data)
        return Response(serializer.data, status.HTTP_200_OK)


class VendorNumberListView(generics.GenericAPIView):
    def get(self, request):
        vendor_numbers = UserProfile.objects.filter(user__in=get_filtered_users(request), vendor_number__isnull=False)
        vendor_numbers = list(vendor_numbers.distinct('vendor_number').values_list('vendor_number', flat=True))

        # Add numbers from travel agents
        travel_agent_vendor_numbers = list(TravelAgent.objects.distinct('code').values_list('code', flat=True))

        vendor_numbers.extend(travel_agent_vendor_numbers)
        vendor_numbers.sort()
        return Response(vendor_numbers, status.HTTP_200_OK)


class PermissionMatrixView(generics.GenericAPIView):
    def get(self, request):
        return Response(PERMISSION_MATRIX, status.HTTP_200_OK)


class SettingsView(generics.GenericAPIView):
    def get(self, request):
        data = {'disable_invoicing': settings.DISABLE_INVOICING}
        return Response(data=data, status=status.HTTP_200_OK)
