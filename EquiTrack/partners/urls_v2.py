from django.conf.urls import patterns, url

from .views.v2 import (
    AgreementListAPIView,
    AgreementDetailAPIView,
    AgreementInterventionsListAPIView,
    PartnerStaffMemberListAPIVIew,
    PartnerStaffMemberDetailAPIView,
    PartnerStaffMemberPropertiesAPIView,
)

urlpatterns = (
    url(r'^agreements/$', view=AgreementListAPIView.as_view(), name='agreement-list'),
    url(r'^agreements/(?P<pk>\d+)/$', view=AgreementDetailAPIView.as_view(), name='agreement-detail'),
    url(r'^agreements/(?P<pk>\d+)/interventions/$', view=AgreementInterventionsListAPIView.as_view(), name='agreement-interventions-list'),
    url(r'^partners/(?P<partner_pk>\d+)/agreements/$', view=AgreementListAPIView.as_view(), name='parter-agreement-list'),
    url(r'^partners/(?P<partner_pk>\d+)/agreements/(?P<pk>\d+)/interventions/$', view=AgreementInterventionsListAPIView.as_view(), name='partner-agreement-interventions-list'),
    url(r'^staff-members/$', view=PartnerStaffMemberListAPIVIew.as_view(), name='staff-member-list'),
    url(r'^staff-members/(?P<pk>\d+)/$', view=PartnerStaffMemberDetailAPIView.as_view(), name='staff-member-detail'),
    url(r'^staff-members/(?P<pk>\d+)/properties/$', view=PartnerStaffMemberPropertiesAPIView.as_view(), name='staff-member-properties'),
    url(r'^partners/(?P<partner_pk>\d+)/staff-members/$', view=PartnerStaffMemberListAPIVIew.as_view(), name='parter-staff-members-list'),
)
