from __future__ import unicode_literals

from collections import OrderedDict
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import connection
from django.db.transaction import atomic
from django.http.response import HttpResponse
from django_fsm import TransitionNotAllowed
from django.views.generic.base import View

from rest_framework import generics, viewsets, mixins, status, views
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.parsers import FormParser, MultiPartParser, FileUploadParser
from rest_framework.permissions import IsAdminUser
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from rest_framework_csv import renderers

from publics.models import TravelExpenseType
from t2f.filters import TravelRelatedModelFilter, TravelActivityPartnerFilter
from t2f.filters import travel_list, action_points, invoices
from users.models import Section
from locations.models import Location
from partners.models import PartnerOrganization, Intervention
from reports.models import Result
from t2f.serializers.export import TravelListExportSerializer, FinanceExportSerializer, TravelAdminExportSerializer, \
    InvoiceExportSerializer

from t2f.models import Travel, TravelAttachment, TravelType, ModeOfTravel, ActionPoint, Invoice, IteneraryItem, \
    InvoiceItem, TravelActivity, TransitionError
from t2f.serializers.travel import TravelListSerializer, TravelDetailsSerializer, TravelAttachmentSerializer, \
    CloneParameterSerializer, CloneOutputSerializer, ActionPointSerializer, TravelActivityByPartnerSerializer
from t2f.serializers.invoices import InvoiceSerializer
from t2f.serializers.static_data import StaticDataSerializer
from t2f.helpers import PermissionMatrix, CloneTravelHelper, FakePermissionMatrix
from t2f.permission_matrix import PERMISSION_MATRIX
from t2f.vision import InvoiceExport, InvoiceUpdater, InvoiceUpdateError


class T2FPagePagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    page_query_param = 'page'

    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('page_count', self.page.paginator.num_pages),
            ('data', data),
            ('total_count', self.page.paginator.object_list.count()),
        ]))


def get_filtered_users(request):
    User = get_user_model()
    return User.objects.exclude(first_name='', last_name='')


def run_transition(serializer):
    transition_name = serializer.transition_name
    if transition_name:
        instance = serializer.instance
        transition = getattr(instance, transition_name)
        try:
            transition()
        except (TransitionNotAllowed, TransitionError) as exc:
            raise ValidationError({'non_field_errors': [exc.message]})
        instance.save()


class TravelListViewSet(mixins.ListModelMixin,
                        mixins.CreateModelMixin,
                        viewsets.GenericViewSet):
    queryset = Travel.objects.all()
    serializer_class = TravelListSerializer
    pagination_class = T2FPagePagination
    permission_classes = (IsAdminUser,)
    filter_backends = (travel_list.TravelSearchFilter,
                       travel_list.ShowHiddenFilter,
                       travel_list.TravelSortFilter,
                       travel_list.TravelFilterBoxFilter)
    renderer_classes = (renderers.JSONRenderer, renderers.CSVRenderer)

    _transition_name_mapping = {'save_and_submit': 'submit_for_approval'}

    @atomic
    def create(self, request, *args, **kwargs):
        if 'transition_name' in kwargs:
            transition_name = kwargs['transition_name']
            request.data['transition_name'] = self._transition_name_mapping.get(transition_name, transition_name)

        serializer = TravelDetailsSerializer(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        super(TravelListViewSet, self).perform_create(serializer)
        run_transition(serializer)

    def export(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serialzier = TravelListExportSerializer(queryset, many=True, context=self.get_serializer_context())

        response = Response(data=serialzier.data, status=status.HTTP_200_OK)
        response['Content-Disposition'] = 'attachment; filename="TravelListExport.csv"'
        return response

    def export_finances(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serialzier = FinanceExportSerializer(queryset, many=True, context=self.get_serializer_context())

        response = Response(data=serialzier.data, status=status.HTTP_200_OK)
        response['Content-Disposition'] = 'attachment; filename="TravelListExport.csv"'
        return response

    def export_travel_admins(self, request, *args, **kwargs):
        travel_queryset = self.filter_queryset(self.get_queryset())
        queryset = IteneraryItem.objects.filter(travel__in=travel_queryset).order_by('travel__reference_number')
        queryset = queryset.prefetch_related('airlines')
        serialzier = TravelAdminExportSerializer(queryset, many=True, context=self.get_serializer_context())

        response = Response(data=serialzier.data, status=status.HTTP_200_OK)
        response['Content-Disposition'] = 'attachment; filename="TravelListExport.csv"'
        return response

    def export_invoices(self, request, *args, **kwargs):
        travel_queryset = self.filter_queryset(self.get_queryset())
        queryset = InvoiceItem.objects.filter(invoice__travel__in=travel_queryset).order_by('invoice__travel__reference_number')
        serialzier = InvoiceExportSerializer(queryset, many=True, context=self.get_serializer_context())

        response = Response(data=serialzier.data, status=status.HTTP_200_OK)
        response['Content-Disposition'] = 'attachment; filename="TravelListExport.csv"'
        return response


class TravelDetailsViewSet(mixins.RetrieveModelMixin,
                           mixins.UpdateModelMixin,
                           viewsets.GenericViewSet):
    queryset = Travel.objects.all()
    serializer_class = TravelDetailsSerializer
    pagination_class = PageNumberPagination
    permission_classes = (IsAdminUser,)
    lookup_url_kwarg = 'travel_pk'

    def get_serializer_context(self):
        context = super(TravelDetailsViewSet, self).get_serializer_context()

        # This will prevent Swagger error because it will not populate self.kwargs with the required arguments to fetch
        # the object.
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        if lookup_url_kwarg in self.kwargs:
            obj = self.get_object()
            context['permission_matrix'] = PermissionMatrix(obj, self.request.user)
        else:
            context['permission_matrix'] = FakePermissionMatrix(self.request.user)

        return context

    @atomic
    def partial_update(self, request, *args, **kwargs):
        if 'transition_name' in kwargs:
            request.data['transition_name'] = kwargs['transition_name']
        return super(TravelDetailsViewSet, self).partial_update(request, *args, **kwargs)

    @atomic
    def perform_update(self, serializer):
        super(TravelDetailsViewSet, self).perform_update(serializer)

        # If invoicing is enabled, do the treshold check, otherwise it will result an infinite process loop
        if not settings.DISABLE_INVOICING and serializer.transition_name == 'send_for_payment' \
                and self.check_treshold(serializer.instance):
            serializer.transition_name = 'submit_for_approval'

        run_transition(serializer)

        # If invoicing is turned off, jump to sent_for_payment when someone approves the travel
        if serializer.transition_name == 'approve' and settings.DISABLE_INVOICING:
            serializer.transition_name = 'send_for_payment'
            run_transition(serializer)

    def check_treshold(self, travel):
        expenses = {'user': Decimal(0),
                    'travel_agent': Decimal(0)}

        for expense in travel.expenses.all():
            if expense.type.vendor_number == TravelExpenseType.USER_VENDOR_NUMBER_PLACEHOLDER:
                expenses['user'] += expense.amount
            elif expense.type.vendor_number:
                expenses['travel_agent'] += expense.amount

        traveler_delta = 0
        travel_agent_delta = 0
        if travel.approved_cost_traveler:
            traveler_delta = expenses['user'] - travel.approved_cost_traveler
            if travel.currency.code != 'USD':
                exchange_rate = travel.currency.exchange_rates.all().last()
                traveler_delta *= exchange_rate.x_rate

        if travel.approved_cost_travel_agencies:
            travel_agent_delta = expenses['travel_agent'] - travel.approved_cost_travel_agencies

        workspace = self.request.user.profile.country
        if workspace.threshold_tre_usd and traveler_delta > workspace.threshold_tre_usd:
            return True

        if workspace.threshold_tae_usd and travel_agent_delta > workspace.threshold_tae_usd:
            return True

        return False

    @atomic
    def clone_for_secondary_traveler(self, request, *args, **kwargs):
        traveler = self._get_traveler_for_cloning()
        helper = CloneTravelHelper(self.get_object())
        clone = helper.clone_for_secondary_traveler(traveler)
        serializer = CloneOutputSerializer(clone, context=self.get_serializer_context())
        return Response(serializer.data, status.HTTP_201_CREATED)

    @atomic
    def clone_for_driver(self, request, *args, **kwargs):
        traveler = self._get_traveler_for_cloning()
        helper = CloneTravelHelper(self.get_object())
        clone = helper.clone_for_driver(traveler)
        serializer = CloneOutputSerializer(clone, context=self.get_serializer_context())
        return Response(serializer.data, status.HTTP_201_CREATED)

    def _get_traveler_for_cloning(self):
        parameter_serializer = CloneParameterSerializer(data=self.request.data)
        parameter_serializer.is_valid(raise_exception=True)
        traveler = parameter_serializer.validated_data['traveler']
        return traveler


class TravelDashboardViewSet(mixins.ListModelMixin,
                             viewsets.GenericViewSet):
    queryset = Travel.objects.all()
    permission_classes = (IsAdminUser,)

    def list(self, request, year, month, **kwargs):
        data = {}

        travels_all = Travel.objects.filter(
            start_date__year=year,
            start_date__month=month,
        )

        office_id = request.query_params.get("office_id", None)
        if office_id:
            travels_all = travels_all.filter(office_id=office_id)

        data["planned"] = travels_all.filter(status=Travel.PLANNED).count()
        data["approved"] = travels_all.filter(status=Travel.APPROVED).count()
        data["completed"] = travels_all.filter(status=Travel.COMPLETED).count()

        section_ids = Travel.objects.all().values_list('section', flat=True).distinct()
        travels_by_section = []
        for section_id in section_ids:
            travels = travels_all.filter(section=section_id)
            if travels.exists():
                planned = travels.filter(status=Travel.PLANNED).count()
                approved = travels.filter(status=Travel.APPROVED).count()
                completed = travels.filter(status=Travel.COMPLETED).count()
                section_trips = {
                    "section_id": travels.first().section.id,
                    "section_name": travels.first().section.name,
                    "planned_travels": planned,
                    "approved_travels": approved,
                    "completed_travels": completed,
                }
                travels_by_section.append(section_trips)

        data["travels_by_section"] = travels_by_section

        return Response(data)


class TravelAttachmentViewSet(mixins.ListModelMixin,
                              mixins.CreateModelMixin,
                              mixins.DestroyModelMixin,
                              viewsets.GenericViewSet):
    queryset = TravelAttachment.objects.all()
    serializer_class = TravelAttachmentSerializer
    parser_classes = (FormParser, MultiPartParser, FileUploadParser)
    permission_classes = (IsAdminUser,)
    filter_backends = (TravelRelatedModelFilter,)
    lookup_url_kwarg = 'attachment_pk'

    def get_serializer_context(self):
        context = super(TravelAttachmentViewSet, self).get_serializer_context()
        # TODO: figure out a better solution for this:
        # Hack to prevent swagger from crashing
        if 'travel_pk' not in self.kwargs:
            return context
        # TODO filter out the travels which cannot be edited (permission check)
        queryset = Travel.objects.all()
        travel = get_object_or_404(queryset, pk=self.kwargs['travel_pk'])
        context['travel'] = travel
        return context


class TravelActivityViewSet(mixins.ListModelMixin,
                            viewsets.GenericViewSet):
    queryset = TravelActivity.objects.all()
    permission_classes = (IsAdminUser,)
    serializer_class = TravelActivityByPartnerSerializer
    filter_backends = (TravelActivityPartnerFilter,)
    lookup_url_kwarg = 'partner_organization_pk'

class ActionPointViewSet(mixins.ListModelMixin,
                         mixins.RetrieveModelMixin,
                         mixins.UpdateModelMixin,
                         viewsets.GenericViewSet):
    queryset = ActionPoint.objects.all()
    serializer_class = ActionPointSerializer
    pagination_class = T2FPagePagination
    permission_classes = (IsAdminUser,)
    filter_backends = (action_points.ActionPointSearchFilter,
                       action_points.ActionPointSortFilter,
                       action_points.ActionPointFilterBoxFilter)
    lookup_url_kwarg = 'action_point_pk'


class ActionPointDashboardViewSet(mixins.ListModelMixin,
                             viewsets.GenericViewSet):
    queryset = ActionPoint.objects.all()
    permission_classes = (IsAdminUser,)

    def list(self, request, **kwargs):
        data = {}

        office_id = request.query_params.get("office_id", None)
        section_ids = Travel.objects.all().values_list('section', flat=True).distinct()
        action_points_by_section = []
        for section_id in section_ids:
            travels = Travel.objects.filter(section=section_id)
            if office_id:
                travels = travels.filter(office_id=office_id)
            if travels.exists():
                action_points = ActionPoint.objects.filter(travel__in=travels)
                total = action_points.count()
                completed = action_points.filter(status=Travel.COMPLETED).count()
                section_action_points = {
                    "section_id": travels.first().section.id,
                    "section_name": travels.first().section.name,
                    "total_action_points": total,
                    "completed_action_points": completed,
                }
                action_points_by_section.append(section_action_points)

        data["action_points_by_section"] = action_points_by_section

        return Response(data)


class InvoiceViewSet(mixins.ListModelMixin,
                     mixins.RetrieveModelMixin,
                     viewsets.GenericViewSet):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    pagination_class = T2FPagePagination
    permission_classes = (IsAdminUser,)
    filter_backends = (invoices.InvoiceSearchFilter,
                       invoices.InvoiceSortFilter,
                       invoices.InvoiceFilterBoxFilter)
    lookup_url_kwarg = 'invoice_pk'


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
        vendor_numbers = [u.profile.vendor_number for u in get_filtered_users(request)]
        # Add numbers from travel agents
        vendor_numbers.extend([])
        vendor_numbers = list(set(vendor_numbers))
        vendor_numbers.sort()
        return Response(vendor_numbers, status.HTTP_200_OK)


class PermissionMatrixView(generics.GenericAPIView):
    def get(self, request):
        return Response(PERMISSION_MATRIX, status.HTTP_200_OK)


class VisionInvoiceExport(View):
    def get(self, request):
        exporter = InvoiceExport()
        xml_structure = exporter.generate_xml()
        return HttpResponse(xml_structure, content_type='application/xml')


class VisionInvoiceUpdate(View):
    def post(self, request):
        updater = InvoiceUpdater(request.body)
        try:
            with atomic():
                updater.update_invoices()
        except InvoiceUpdateError as exc:
            return HttpResponse('\n'.join(exc.errors), status=status.HTTP_400_BAD_REQUEST)
        return HttpResponse()


class SettingsView(generics.GenericAPIView):
    def get(self, request):
        data = {'disable_invoicing': settings.DISABLE_INVOICING}
        return Response(data=data, status=status.HTTP_200_OK)
