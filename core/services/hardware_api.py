# -*- coding: utf-8 -*-
__author__ = 'Nikolay Mamashin (mamashin@gmail.com)'

import json
from core.models import MqttTopic
from loguru import logger
import httpx
from decouple import config # noqa
import paho.mqtt.publish as publish
from django.core.cache import cache


def publish_to_mqtt(topic, payload):
    try:
        publish.single(topic, payload=json.dumps(payload).encode(), hostname="localhost")
    except Exception as e:
        logger.error(f"Error publish to MQTT broker - {e}")
    return


def write_to_cache(topic, payload, ttl: int = 360):
    cache.set(topic, payload, ttl)


def make_hw_api_request(mqtt_data: MqttTopic, cmd: str = 'status') -> dict:
    response_status = {'ok': False}

    def error_handler(message):
        logger.error(message)
        response_status['msg'] = message
        return response_status

    hw_ctrl_api_url = config("HW_CTRL_API_URL")
    base_uri = f'{hw_ctrl_api_url}/{mqtt_data.group_name}'
    if not cmd or cmd not in ['on', 'off', 'toggle', 'status']:
        return response_status
    if mqtt_data.group_name in ['relay', 'input']:
        base_uri = f'{base_uri}/{mqtt_data.unit_id}/{mqtt_data.channel}'
    if mqtt_data.group_name in ['w1', 'sensor']:  # If it Wire1 or other sensor
        base_uri = f'{base_uri}/{mqtt_data.topic}'

    base_uri = f'{base_uri}?cmd={cmd}'

    try:
        hw_api_response = httpx.get(base_uri, timeout=4, headers={'Connection': 'close'})
    except Exception as e:
        return error_handler(f'Unable connect to {base_uri} - {e}')
    if not str(hw_api_response.status_code).startswith("2"):
        return error_handler(f"Got response error from MQTT API - {hw_api_response.text}")
    try:
        hw_api_response_dict = hw_api_response.json()
    except Exception as e:
        return error_handler(f"Unable convert response to JSON - {e} ({hw_api_response.text})")
    if hw_api_response_dict.get('error'):
        return error_handler(f"Что-то не то при запросе ModBus API - {hw_api_response_dict}")

    response_status['ok'] = True
    response_status['data'] = hw_api_response_dict.get('data')

    publish_to_mqtt(f'{mqtt_data.group_name}/{mqtt_data.topic}', response_status['data'])
    write_to_cache(f'{mqtt_data.group_name}/{mqtt_data.topic}', response_status['data'])

    return response_status
