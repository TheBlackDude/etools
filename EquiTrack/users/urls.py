__author__ = 'jcranwellward'

from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView

from .views import UserAuthAPIView, ProfileEdit, UsersView


urlpatterns = patterns(
    '',

    #api
    url(r'^api/profile/$', UserAuthAPIView.as_view()),
    url(r'^api/$', UsersView.as_view()),

    #user profile
    url(r'^profile_view/$', ProfileEdit.as_view(), name='user_profile'),

    url(r'^profile_view/complete/$',
        TemplateView.as_view(
            template_name='users/profile_change_done.html'),
        name='profile_complete'),
)