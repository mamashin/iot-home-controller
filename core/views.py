# -*- coding: utf-8 -*-

__author__ = 'Nikolay Mamashin (mamashin@gmail.com)'

from django.shortcuts import render
from django.views.generic import CreateView, TemplateView, ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from decouple import config
from django.db.models.expressions import F


class MainPage(TemplateView):
    template_name = "main.html"
    context_object_name = "result"
