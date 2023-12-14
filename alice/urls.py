# -*- coding: utf-8 -*-

__author__ = 'Nikolay Mamashin (mamashin@gmail.com)'

from django.urls import path, include
from .views import RootHead, GetDevices, UnlinkPost, DevicesQueryOrActionPost
import oauth2_provider.views as oauth2_views


urlpatterns = [
    path('v1.0/user/unlink', UnlinkPost.as_view()),
    path('v1.0/user/devices/query', DevicesQueryOrActionPost.as_view(), {'request_type': 'query'}),
    path('v1.0/user/devices/action', DevicesQueryOrActionPost.as_view(), {'request_type': 'action'}),
    path('v1.0/user/devices', GetDevices.as_view()),
    path('v1.0', RootHead.as_view()),

    path('auth/', oauth2_views.AuthorizationView.as_view(), name="auth"),
    path('token/', oauth2_views.TokenView.as_view(), name="token"),
    path('revoke-token/', oauth2_views.RevokeTokenView.as_view(), name="revoke-token"),

]
