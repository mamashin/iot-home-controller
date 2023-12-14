from django.shortcuts import render

from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import AliceDeviceSerializer, AliceDevicesQuerySerializer, AliceDevicesActionSerializer
from core.models import MqttTopic
from .services import make_alice_device_list, parse_devices_query_or_action
from oauth2_provider.contrib.rest_framework import OAuth2Authentication, TokenHasReadWriteScope
from loguru import logger


class RootHead(APIView):
    permission_classes = [AllowAny]
    http_method_names = ['head']

    def head(self, request, *args, **kwargs):
        return Response({}, status=204)


class UnlinkPost(APIView):
    authentication_classes = [OAuth2Authentication]
    permission_classes = [TokenHasReadWriteScope]
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        return Response({})


class GetDevices(APIView):
    authentication_classes = [OAuth2Authentication]
    permission_classes = [TokenHasReadWriteScope]

    def get(self, request, *args, **kwargs):
        request_id = request.headers.get('X-Request-Id')
        if not request_id:
            return Response({'message': 'Luk ? Its you ?'}, status=401)
        rsp = {
            "request_id": request_id,
            "payload": {
                "user_id": f'{request.user.username}_{request.user.id}',
                "devices": make_alice_device_list()
            }
        }
        return Response(rsp)


class DevicesQueryOrActionPost(APIView):
    authentication_classes = [OAuth2Authentication]
    permission_classes = [TokenHasReadWriteScope]
    http_method_names = ['post']
    serializer_class = AliceDevicesQuerySerializer

    def post(self, request, *args, **kwargs):
        logger.info(kwargs)
        request_id = request.headers.get('X-Request-Id')
        if not request_id:
            return Response({'message': 'Luk ? Its you ?'}, status=401)

        request_type = kwargs.get('request_type')
        serialized = AliceDevicesQuerySerializer(data=request.data)
        if request_type == 'action':
            serialized = AliceDevicesActionSerializer(data=request.data)

        if not serialized.is_valid():
            logger.info(serialized)
            return Response({'msg': 'Request format error'}, status=403)

        all_dev_response = {
            "request_id": request_id,
            "payload": {
                "devices": parse_devices_query_or_action(serialized.validated_data, request_type)
            }
        }
        return Response(all_dev_response)
