__author__ = 'jcranwellward'

from django.conf.urls import patterns, url

from djgeojson.views import GeoJSONLayerView

from .models import Governorate, Region, Locality
from locations import views


urlpatterns = patterns(
    '',
    url(r'^governorates.geojson$',
        GeoJSONLayerView.as_view(
            model=Governorate,
            properties=['name', 'color']
        ),
        name='governorates',
    ),
    url(r'^districts.geojson$',
        GeoJSONLayerView.as_view(
            model=Region,
            properties=['name', 'color']
        ),
        name='districts'),
    url(r'^sub-districts.geojson$',
        GeoJSONLayerView.as_view(
            model=Locality,
            properties=['name', 'color']
        ),
        name='sub-districts'),
    url(r'^location$', 'locations.views.gateway_model_select'),
    url(r'^location/(?P<gateway>[-\w]+)/all_json_models/$', views.all_json_models),
    url(r'^cartodbtables/$', views.CartoDBTablesView.as_view())
)
