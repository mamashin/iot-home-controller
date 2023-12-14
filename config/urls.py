# -*- coding: utf-8 -*-

__author__ = 'Nikolay Mamashin (mamashin@gmail.com)'

from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include, re_path


urlpatterns = [
    path('api/', include('core.api.urls')),
    path('admin/', admin.site.urls),

    path('o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    path('alice/', include('alice.urls')),
    path('', include('core.urls')),
]
