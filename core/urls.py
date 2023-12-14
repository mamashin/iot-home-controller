# -*- coding: utf-8 -*-

__author__ = 'Nikolay Mamashin (mamashin@gmail.com)'

from django.urls import path, include
from .views import MainPage

urlpatterns = [
    path('', MainPage.as_view()),
]
