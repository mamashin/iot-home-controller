# -*- coding: utf-8 -*-

__author__ = 'Nikolay Mamashin (mamashin@gmail.com)'

from django.apps import AppConfig
from django.utils.module_loading import autodiscover_modules
from datetime import datetime
from django.conf import settings


class CoreConfig(AppConfig):
    name = 'core'

    def ready(self):
        # Automatically import all receivers files
        autodiscover_modules('receivers')
