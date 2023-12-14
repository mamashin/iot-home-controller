# -*- coding: utf-8 -*-
__author__ = 'Nikolay Mamashin (mamashin@gmail.com)'

from loguru import logger

from .hardware_api import make_hw_api_request
from ..api.serializers import RawMqttSerializer
from core.models import MqttTopic, RcCode
from decouple import config  # noqa

DEBUG = config('MQTT_DEBUG', default=False, cast=bool)


def switch_roll(topic: str):
    """
    If it's roll and command "up" - send "off" to "down" and vice versa
    """
    switch_topic = f"{topic[:-5]}_up"
    if topic.endswith("_up"):
        switch_topic = f"{topic[:-3]}_down"
    switch_topic_detail = MqttTopic.objects.filter(topic=switch_topic).first()
    if DEBUG:
        logger.debug(f"Switch topic detail - {switch_topic_detail}")
    if not switch_topic_detail:
        logger.error(f"Unable to find topic for switch roll - {switch_topic}")
        return
    make_hw_api_request(switch_topic_detail, "off")


def parse_raw_mqtt(mqtt_data: RawMqttSerializer.validated_data) -> dict:
    response_status = {'ok': False}
    if DEBUG:
        logger.debug(mqtt_data)
    request_topic = mqtt_data['topic']
    topic_db_data = MqttTopic.objects.filter(topic=request_topic).first()
    cmd = 'status'  # default

    if request_topic == 'rc_code':
        # Если прилетел RC с пульта - находим его в базе и дальше уже обрабатываем топик который к нему привязан
        if not mqtt_data.get('payload') or not mqtt_data.get('payload').get('data'):
            logger.error('No RC code in payload data')
            return response_status
        raw_code = mqtt_data.get('payload').get('data')
        rc_code_data = RcCode.objects.filter(code=raw_code).first()
        if not rc_code_data:
            logger.info(f'RC code "{raw_code}" not found..')
            return response_status
        topic_db_data = rc_code_data.topic
        cmd = "toggle"

    if request_topic != 'rc_code':
        if not mqtt_data.get('payload') or not mqtt_data.get('payload').get('cmd'):
            logger.error(f'No cmd in payload found')
            return response_status
        cmd = mqtt_data.get('payload').get('cmd')

    if '/' in request_topic:
        # If topic looks like 'relay/room_main_right_light'
        split_topic = request_topic.split('/')
        request_topic = split_topic[1]
        request_group = split_topic[0]
        topic_db_data = MqttTopic.objects.filter(topic=request_topic, group__group=request_group).first()

    if not topic_db_data:
        response_status['msg'] = 'Topic not found'
        return response_status

    if topic_db_data.group_name in ['relay', 'input']:  # Если это реле или input - значит обязательно должны быть unit
        if not topic_db_data.unit_id and not topic_db_data.channel:
            msg = "No Unit and channel define! Exit."
            logger.error(msg)
            response_status['msg'] = msg
            return response_status

    if topic_db_data.topic.startswith('roll_') and cmd in ['on', 'toggle']:
        switch_roll(topic_db_data.topic)

    result_hw_api_request = make_hw_api_request(topic_db_data, cmd)
    if DEBUG:
        logger.warning(result_hw_api_request)

    return result_hw_api_request
