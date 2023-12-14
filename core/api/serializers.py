# -*- coding: utf-8 -*-

__author__ = 'Nikolay Mamashin (mamashin@gmail.com)'

from rest_framework import serializers
from core.models import MqttTopic, RcCode


class MqttTopicSerializer(serializers.ModelSerializer):
    group = serializers.SlugRelatedField(many=False, read_only=True, slug_field='group')

    class Meta:
        model = MqttTopic
        # fields = '__all__'
        exclude = ['id', 'alice', 'alice_data']


class RcCodeSerializer(serializers.ModelSerializer):
    # topic = serializers.SlugRelatedField(many=False, read_only=True, slug_field='topic')
    result = MqttTopicSerializer(many=False, read_only=True, source='topic')

    class Meta:
        model = RcCode
        # exclude = ('id', )
        fields = ('result',)


class RawMqttSerializer(serializers.Serializer):
    topic = serializers.CharField(max_length=255, required=True)
    payload = serializers.JSONField(required=False)
