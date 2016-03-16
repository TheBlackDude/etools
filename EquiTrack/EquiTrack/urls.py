from __future__ import absolute_import

from django.conf import settings
from django.conf.urls import patterns, include, url
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import REDIRECT_FIELD_NAME

from autocomplete_light import shortcuts as autocomplete_light
# import every app/autocomplete_light_registry.py
autocomplete_light.autodiscover()

from rest_framework_nested import routers

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

from .utils import staff_required
from .views import (
    MainView,
    MapView,
    DashboardView,
    UserDashboardView,
    CmtDashboardView,
)
from trips.views import TripsViewSet, Trips2ViewSet
from partners.views import InterventionsViewSet, IndicatorReportViewSet
from partners.views import PartnerOrganizationsViewSet, AgreementViewSet, PartnerStaffMembersViewSet

from partners.urls import (
    interventions_api,
    results_api,
    reports_api,
    pcasectors_api,
    pcabudgets_api,
    pcafiles_api,
    pcagrants_api
)

api = routers.SimpleRouter()
api.register(r'trips', TripsViewSet, base_name='trip')
api.register(r'trips2', Trips2ViewSet, base_name='trip2')
api.register(r'partnerorganizations', PartnerOrganizationsViewSet, base_name='partnerorganizations')
api.register(r'partnerstaffmemebers', PartnerStaffMembersViewSet, base_name='partnerstaffmemebers')
api.register(r'agreements', AgreementViewSet, base_name='agreements')


urlpatterns = patterns(
    '',
    # TODO: overload login_required to staff_required to automatically re-route partners to the parter portal
    url(r'^$', staff_required(UserDashboardView.as_view()), name='dashboard'),
    url(r'^login/$', MainView.as_view(), name='main'),
    url(r'^indicators', login_required(DashboardView.as_view()), name='indicator_dashboard'),
    url(r'^map/$', login_required(MapView.as_view()), name='map'),
    url(r'^cmt/$', login_required(CmtDashboardView.as_view()), name='cmt'),

    url(r'^locations/', include('locations.urls')),
    url(r'^management/', include('management.urls')),
    url(r'^partners/', include('partners.urls')),
    url(r'^trips/', include('trips.urls')),
    url(r'^users/', include('users.urls')),
    url(r'^supplies/', include('supplies.urls')),

    url(r'^api/', include(api.urls)),
    url(r'^api/', include(interventions_api.urls)),
    url(r'^api/', include(results_api.urls)),
    url(r'^api/', include(pcasectors_api.urls)),
    url(r'^api/', include(pcabudgets_api.urls)),
    url(r'^api/', include(pcafiles_api.urls)),
    url(r'^api/', include(pcagrants_api.urls)),
    url(r'^api/', include(reports_api.urls)),
    url(r'^api/docs/', include('rest_framework_swagger.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # helper urls
    url(r'^accounts/', include('allauth.urls')),
    url(r'^saml2/', include('djangosaml2.urls')),
    url(r'^chaining/', include('smart_selects.urls')),
    url(r'^autocomplete/', include('autocomplete_light.urls')),
    url(r'^login/token-auth/', 'rest_framework_jwt.views.obtain_jwt_token'),
    url(r'^api-token-auth/', 'rest_framework_jwt.views.obtain_jwt_token'),  # TODO: remove this when eTrips is deployed needed
)


if settings.DEBUG:
    import debug_toolbar

    urlpatterns += patterns(
        '',
        url(r'^__debug__/', include(debug_toolbar.urls)),
        url(r'^test/', 'djangosaml2.views.echo_attributes'),
    )
