from __future__ import absolute_import

__author__ = 'jcranwellward'

from datetime import datetime
from rest_framework.generics import ListAPIView

from locations.models import Location
from .serializers import LocationSerializer, PartnershipSerializer

from partners.models import (
    PCA,
    PCAGrant,
    PCASector,
    GwPCALocation
)


class PcaView(ListAPIView):

    model = PCA
    serializer_class = PartnershipSerializer

    def get_queryset(self):
        """
        Return locations with GPS points only
        """
        status = self.request.query_params.get('status', None)
        result_structure = self.request.query_params.get('result_structure', None)
        sector = self.request.query_params.get('sector', None)
        gateway = self.request.query_params.get('gateway', None)
        governorate = self.request.query_params.get('governorate', None)
        donor = self.request.query_params.get('donor', None)
        partner = self.request.query_params.get('partner', None)
        district = self.request.query_params.get('district', None)
        from_date = self.request.query_params.get('from_date', None)
        to_date = self.request.query_params.get('to_date', None)

        queryset = self.model.objects.filter(
            current=True,
        )

        if status is not None:
            queryset = self.model.objects.filter(status=status)

        if gateway is not None:
            # queryset = queryset.filter(
            #     location__gateway__id=int(gateway)
            # )
            pca_ids = GwPCALocation.objects.filter(location__gateway__id=int(gateway)).values_list('id', flat=True)
            queryset = queryset.filter(
                id__in=pca_ids
            )
        if governorate is not None:
            pca_ids = GwPCALocation.objects.filter(governorate=governorate).values_list('id', flat=True)
            queryset = queryset.filter(
                id__in=pca_ids
            )

        if district is not None:
            queryset = queryset.filter(
                region__id=int(district)
            )
        if result_structure is not None:
            queryset = queryset.filter(
                result_structure__id=int(result_structure)
            )
        if partner is not None:
            queryset = queryset.filter(
                partner__id=int(partner)
            )
        if sector is not None:
            # get the filtered pcas so far
            pcas = queryset.values_list('id', flat=True)
            # get those that contain this sector
            pcas = PCASector.objects.filter(
                pca__in=pcas,
                sector__id=int(sector)
            ).values_list('pca__id', flat=True)
            # now filter the current query by the selected ids
            queryset = queryset.filter(
                id__in=pcas
            )

        if donor is not None:
            # get the filtered pcas so far
            pcas = queryset.values_list('id', flat=True)
            # get those that contain this donor
            pcas = PCAGrant.objects.filter(
                pca__id__in=pcas,
                grant__donor__id=int(donor)
            ).values_list('pca', flat=True)
            # now filter the current query by the selected ids
            queryset = queryset.filter(
                id__in=pcas
            )

        if from_date is not None and to_date is not None:
            fdate = datetime.strptime(from_date, '%m/%d/%Y').date()
            tdate = datetime.strptime(to_date, '%m/%d/%Y').date()
            queryset = queryset.filter(
                end_date__range=(fdate, tdate)
            )

        return queryset


class LocationView(ListAPIView):

    model = GwPCALocation
    serializer_class = LocationSerializer

    def get_queryset(self):
        """
        Return locations with GPS points only
        """
        status = self.request.query_params.get('status', PCA.ACTIVE)
        result_structure = self.request.query_params.get('result_structure', None)
        sector = self.request.query_params.get('sector', None)
        gateway = self.request.query_params.get('gateway', None)
        governorate = self.request.query_params.get('governorate', None)
        donor = self.request.query_params.get('donor', None)
        partner = self.request.query_params.get('partner', None)
        district = self.request.query_params.get('district', None)

        queryset = self.model.objects.filter(
            pca__status=status,
            pca__current=True,
            location__point__isnull=False
        )

        if gateway is not None:
            queryset = queryset.filter(
                location__gateway__id=int(gateway)
            )
        if governorate is not None:
            queryset = queryset.filter(
                governorate__id=int(governorate)
            )
        if district is not None:
            queryset = queryset.filter(
                region__id=int(district)
            )
        if result_structure is not None:
            queryset = queryset.filter(
                pca__result_structure__id=int(result_structure)
            )
        if partner is not None:
            queryset = queryset.filter(
                pca__partner__id=int(partner)
            )
        if sector is not None:
            # get the filtered pcas so far
            pcas = queryset.values_list('pca__id', flat=True)
            # get those that contain this sector
            pcas = PCASector.objects.filter(
                pca__in=pcas,
                sector__id=int(sector)
            ).values_list('pca__id', flat=True)
            # now filter the current query by the selected ids
            queryset = queryset.filter(
                pca__id__in=pcas
            )

        if donor is not None:
            # get the filtered pcas so far
            pcas = queryset.values_list('pca__id', flat=True)
            # get those that contain this donor
            pcas = PCAGrant.objects.filter(
                pca__id__in=pcas,
                grant__donor__id=int(donor)
            ).values_list('pca', flat=True)
            # now filter the current query by the selected ids
            queryset = queryset.filter(
                pca__id__in=pcas
            )

        pca_locs = queryset.values_list('location', flat=True)
        locs = Location.objects.filter(
            id__in=pca_locs
        )
        return locs


