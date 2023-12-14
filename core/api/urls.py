# -*- coding: utf-8 -*-

__author__ = 'Nikolay Mamashin (mamashin@gmail.com)'

from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from rest_framework import routers

from core.api.viewsets import MqttTopicGet, RcCodeGet, TopicGet, RawMqttPost

urlpatterns = [
    path('mqtt/', MqttTopicGet.as_view()),
    path('rawmqtt/', RawMqttPost.as_view()),
    re_path('code/(?P<code>.+)/$', RcCodeGet.as_view()),
    re_path('topic/(?P<mqtt>.+)/$', TopicGet.as_view()),
]
