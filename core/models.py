# -*- coding: utf-8 -*-
import secrets
import string

from django.db import models
from django.utils import timezone
import time
from django.contrib.auth.models import User


def randon_string_id():
    return ''.join((secrets.choice(string.ascii_letters + string.digits) for i in range(8)))


class MqttGroup(models.Model):
    group = models.CharField(blank=False, verbose_name="Group Name", null=False, max_length=255)

    def __str__(self):
        return f"{self.group}"


class MqttTopic(models.Model):
    group = models.ForeignKey(MqttGroup, null=True, blank=True, on_delete=models.DO_NOTHING)
    topic = models.CharField(blank=False, verbose_name="Topic Name", null=False, max_length=255, unique=True)
    unit_id = models.IntegerField(blank=True, null=True, verbose_name="Unit ID")
    channel = models.IntegerField(blank=True, null=True, verbose_name="Channel")
    description = models.CharField(blank=True, verbose_name="Description", null=True, max_length=255)
    alice = models.BooleanField(default=False, verbose_name="Алиса")
    alice_data = models.JSONField(default=dict, verbose_name="Alice Data Json", blank=False)
    alice_name = models.CharField(blank=True, verbose_name="Alice Name", null=True, max_length=255)
    alice_room = models.CharField(blank=True, verbose_name="Alice Room", null=True, max_length=255)
    str_id = models.CharField(blank=True, verbose_name="String ID", max_length=8, unique=True, default=randon_string_id)

    @property
    def group_name(self):
        return str(self.group)

    @property
    def alice_data_count(self):
        cnt = len(self.alice_data)
        if cnt > 0:
            return cnt
        return '-'

    # class Meta:
    #     unique_together = ['unit_id', 'channel']

    def __str__(self):
        return f"{self.group} / {self.topic} || {self.description}"


class RcCode(models.Model):
    code = models.CharField(blank=False, verbose_name="RC RAW code", null=False, max_length=255,
                            unique=True, db_index=True)
    topic = models.ForeignKey(MqttTopic, null=True, blank=False, on_delete=models.CASCADE)
    description = models.CharField(blank=True, verbose_name="Description", null=True, max_length=255)

    def __str__(self):
        return f"{self.code} / {self.topic}"
