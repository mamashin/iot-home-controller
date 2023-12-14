# -*- coding: utf-8 -*-

__author__ = 'Nikolay Mamashin (mamashin@gmail.com)'

from django.contrib.auth.middleware import RemoteUserMiddleware
from django.contrib.auth.backends import RemoteUserBackend


class CustomRemoteUserMiddleware(RemoteUserMiddleware):
    # header = 'HTTP_AUTHUSER'
    header = 'REMOTE_USER'


class CustomRemoteUserBackend(RemoteUserBackend):
    create_unknown_user = False
