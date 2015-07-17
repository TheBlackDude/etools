__author__ = 'jcranwellward'

from django.conf.urls import patterns, url

from .views import (
    LocationView,
    ValidatePCANumberView,
    CreateFACERequestView,
    PcaView
)


urlpatterns = patterns(
    '',
    url(r'locations/$', LocationView.as_view(), name='locations'),
    url(r'pcas/$', PcaView.as_view(), name='pcas'),
    url(r'pca/validate/$', ValidatePCANumberView.as_view()),
    url(r'face/create/$', CreateFACERequestView.as_view())
)
