from __future__ import absolute_import

__author__ = 'jcranwellward'


from django.views.generic import TemplateView, View
from django.utils.http import urlsafe_base64_decode
from django.http import HttpResponse
from django.conf import settings
from django.shortcuts import get_object_or_404

from rest_framework.generics import ListAPIView, RetrieveAPIView
from easy_pdf.views import PDFTemplateView

from locations.models import Location
from .serializers import (
    LocationSerializer,
    PartnershipSerializer,
    PartnerStaffMemberPropertiesSerializer,
)

from .models import (
    Agreement,
    AuthorizedOfficer,
    PCA,
    PCAGrant,
    PCASector,
    GwPCALocation,
    PartnerStaffMember
)


class PcaPDFView(PDFTemplateView):
    template_name = "partners/pca_pdf.html"

    def get_context_data(self, **kwargs):
        agr_id = self.kwargs.get('agr')
        agreement = Agreement.objects.get(id=agr_id)
        officers = agreement.authorized_officers.all().values_list('officer', flat=True)
        officers_list = []
        for id in officers:
            officer = AuthorizedOfficer.objects.get(id=id)
            officers_list.append(
                {'first_name': officer.officer.first_name,
                 'last_name': officer.officer.last_name,
                 'title': officer.officer.title}
            )

        return super(PcaPDFView, self).get_context_data(
            pagesize="Letter",
            title="Partnership",
            agreement=agreement,
            auth_officers=officers_list,
            **kwargs
        )


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


class PortalDashView(View):

    def get(self, request):
        with open(settings.SITE_ROOT + '/templates/frontend/partner/partner.html', 'r') as my_f:
            result = my_f.read()
        return HttpResponse(result)


class PartnerStaffMemberPropertiesView(RetrieveAPIView):

    serializer_class = PartnerStaffMemberPropertiesSerializer
    queryset = PartnerStaffMember.objects.all()

    def get_object(self):
        queryset = self.get_queryset()
        # TODO: see permissions if user is staff allow access to all partners (maybe)

        # Get the current partnerstaffmember
        try:
            current_member = PartnerStaffMember.objects.get(id=self.request.user.profile.partner_staff_member)
        except PartnerStaffMember.DoesNotExist:
            raise Exception('there is no PartnerStaffMember record associated with this user')

        # Perform the lookup filtering.
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        # If current member is actually looking for themselves return right away.
        if self.kwargs[lookup_url_kwarg] == str(current_member.id):
            return current_member


        filter = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
        # allow lookup only for PSMs inside the same partnership
        filter['partner'] = current_member.partner

        obj = get_object_or_404(queryset, **filter)
        self.check_object_permissions(self.request, obj)
        return obj


class PartnerInterventionsView(ListAPIView):

    serializer_class = PartnershipSerializer #PartnerInterventionsSerializer
    model = PCA

    def get_queryset(self):
        # get the current user staff member
        try:
            current_member = PartnerStaffMember.objects.get(id=self.request.user.profile.partner_staff_member)
        except PartnerStaffMember.DoesNotExist:
            raise Exception('there is no PartnerStaffMember record associated with this user')

        return current_member.partner.pca_set.all()


class PortalLoginFailedView(TemplateView):

    template_name = "partner_loginfailed.html"

    def get_context_data(self, **kwargs):
        context = super(PortalLoginFailedView, self).get_context_data(**kwargs)
        context['email'] = urlsafe_base64_decode(context['email'])
        return context
