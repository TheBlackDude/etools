
from django.conf.urls import patterns, url

from .views import (
    MyProfileAPIView,
    CountryView
)


urlpatterns = patterns(
    '',
    url(r'^myprofile/$', MyProfileAPIView.as_view(), name="myprofile-detail"),
    url(r'^country/$', CountryView.as_view(http_method_names=['get']), name="country-detail"),

)
