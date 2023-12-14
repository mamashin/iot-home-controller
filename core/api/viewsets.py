# -*- coding: utf-8 -*-

__author__ = 'Nikolay Mamashin (mamashin@gmail.com)'

from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from decouple import config # noqa
from rest_framework.permissions import AllowAny

from .serializers import MqttTopicSerializer, RcCodeSerializer, RawMqttSerializer
from core.models import MqttTopic, RcCode
from ..services.hardware_api import make_hw_api_request
from ..services.raw_mqtt import parse_raw_mqtt


class MqttTopicGet(ListAPIView):
    permission_classes = [AllowAny]
    http_method_names = ['get']
    serializer_class = MqttTopicSerializer

    def get_queryset(self):
        queryset = MqttTopic.objects.all()
        topic = self.request.query_params.get('code')
        if topic is not None:
            queryset = MqttTopic.objects.filter(topic=topic)
        return queryset


class RcCodeGet(RetrieveAPIView):
    permission_classes = [AllowAny]
    http_method_names = ['get']
    serializer_class = RcCodeSerializer
    lookup_field = 'code'
    lookup_url_kwarg = 'code'
    queryset = RcCode.objects.all()


class TopicGet(RetrieveAPIView):
    permission_classes = [AllowAny]
    http_method_names = ['get']
    serializer_class = MqttTopicSerializer
    lookup_field = 'topic'
    lookup_url_kwarg = 'mqtt'
    queryset = MqttTopic.objects.all()


class RawMqttPost(APIView):
    permission_classes = [AllowAny]
    http_method_names = ['post']
    serializer_class = RawMqttSerializer

    def post(self, request, *args, **kwargs):  # noqa
        serialized = self.serializer_class(data=request.data)
        if not serialized.is_valid():
            return Response({'msg': 'Oops'}, status=400)

        mqtt_data = parse_raw_mqtt(serialized.validated_data)
        if not mqtt_data.get('ok'):
            return Response(mqtt_data)
        # return Response(make_hw_request(mqtt_data.get('data'), serialized.validated_data.get('payload')))
        return Response(mqtt_data)
