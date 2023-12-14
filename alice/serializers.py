# -*- coding: utf-8 -*-

__author__ = 'Nikolay Mamashin (mamashin@gmail.com)'

from rest_framework import serializers
from core.models import MqttTopic


class AliceData(serializers.JSONField):
    pass


class AliceDeviceSerializer(serializers.ModelSerializer):
    # group = serializers.SlugRelatedField(many=False, read_only=True, slug_field='group')

    class Meta:
        model = MqttTopic
        # fields = '__all__'
        exclude = ['id', ]


class AliceSingeDeviceQuery(serializers.Serializer):
    id = serializers.CharField(max_length=16, required=True)
    custom_data = serializers.JSONField(required=False)
    capabilities = serializers.JSONField(required=False)


class AliceDevicesQuerySerializer(serializers.Serializer):
    devices = AliceSingeDeviceQuery(many=True)


class AliceDevicesActionSerializer(serializers.Serializer):
    payload = AliceDevicesQuerySerializer(many=False)
