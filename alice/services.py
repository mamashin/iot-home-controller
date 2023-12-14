# -*- coding: utf-8 -*-
__author__ = 'Nikolay Mamashin (mamashin@gmail.com)'

from core.models import MqttTopic
from core.services.hardware_api import make_hw_api_request
from django.core.cache import cache
from loguru import logger


def make_alice_device_list() -> list:
    # Get devices list for request 'GET v1.0/user/devices'
    summary_list = []
    for dev_model in MqttTopic.objects.filter(alice=True, alice_data__has_key='type'):
        device_dict = {
            'type': dev_model.alice_data.get('type'),
            'id': dev_model.str_id,
            'name': dev_model.alice_name,
            'description': dev_model.description,
            'room': dev_model.alice_room,
            'custom_data': {'mqtt': f'{dev_model.group_name}/{dev_model.topic}'},
            'capabilities': [],
            'properties': []
        }

        if all_capabilities := dev_model.alice_data.get('capabilities'):
            for single_cap_dict in all_capabilities:
                device_dict['capabilities'].append(single_cap_dict)

        if all_properties := dev_model.alice_data.get('properties'):
            for single_prop_dict in all_properties:
                device_dict['properties'].append(single_prop_dict)

        summary_list.append(device_dict)

    return summary_list


def error_handler(dev_id: str) -> dict:
    return {
            "id": dev_id,
            "error_code": "DEVICE_UNREACHABLE",
            "error_message": "Error device configure :("
        }


def devices_properties_float(device_db: MqttTopic, instance: str = None) -> dict:
    # Get current device state (properties - devices.properties.float)
    cache_reply = cache.get(f'{device_db.group_name}/{device_db.topic}')
    if cache_reply:
        status_reply = cache_reply
    else:
        status_reply = make_hw_api_request(device_db, cmd='status')
        if not status_reply.get('ok'):
            logger.error(f'Not OK from HW status - {status_reply}')
            return {}
        status_reply = status_reply.get('data')

    if 'status' in status_reply:
        # If this is 'raw' data from relay or input - convert it to format for Alice.
        # 'multiple' - multiplier, custom parameter in Alice settings, if not - then 1,
        # example: if there is voltage in the socket, the sensor will show 'status': 1, and we want Alice to see 220
        status_reply = {
            'value': status_reply.get('status') * (device_db.alice_data.get('multiple') or 1),
            'instance': instance
        }

    return status_reply


def device_state_cap_on_off(device_db: MqttTopic) -> dict:
    # Get current device state (capabilities - devices.capabilities.on_off)
    cache_reply = cache.get(f'{device_db.group_name}/{device_db.topic}')
    if cache_reply:
        logger.info(f"from cache !")
        status_value = cache_reply.get('status') == 1
    else:
        status_reply = make_hw_api_request(device_db, cmd='status')
        if not status_reply.get('ok'):
            logger.error(f'Not OK from HW status - {status_reply}')
            return {}
        status_value = status_reply.get('data').get('status') == 1
    return {
        "instance": "on",
        "value": status_value
    }


def device_action_cap_on_off(device_db: MqttTopic, state: dict) -> dict:
    # Set new device state (capabilities - devices.capabilities.on_off)
    command = 'on' if state.get('value') else 'off'
    status_reply = make_hw_api_request(device_db, cmd=command)

    action_result = {
        "status": "DONE"
    }
    if not status_reply.get('ok'):
        action_result = {
            "status": "ERROR",
            "error_code": "DEVICE_UNREACHABLE",
            "error_message": "Can't set new state :("
        }

    return {
        "instance": "on",
        "action_result": action_result
    }


def query_single_device_state(device_db: MqttTopic):
    devices_capabilities_list = device_db.alice_data.get('capabilities') or []
    devices_properties_list = device_db.alice_data.get('properties') or []
    if not devices_capabilities_list and not devices_properties_list:
        # ! В настройках не заданы и не свойства и не умения
        logger.error('no cap or prop !')
        return error_handler(device_db.str_id)

    return_capabilities = []
    return_properties = []

    # Walk through the abilities (capabilities)
    for single_capabilities in devices_capabilities_list:
        devices_capabilities = single_capabilities.get('type')
        state = {}
        if not devices_capabilities:
            return error_handler(device_db.str_id)
        if devices_capabilities == 'devices.capabilities.on_off':
            state = device_state_cap_on_off(device_db)

        if not state:
            return {}

        return_capabilities.append({
            "type": devices_capabilities,
            "state": state
        })

    # Walk through the properties
    for single_properties in devices_properties_list:
        logger.info(single_properties)
        devices_properties = single_properties.get('type')
        state = {}
        if not devices_properties:
            return error_handler(device_db.str_id)
        if devices_properties == 'devices.properties.float':
            state = devices_properties_float(device_db, single_properties.get('parameters').get('instance'))

        if not state:
            return {}

        return_properties.append({
            "type": devices_properties,
            "state": state
        })

    # Return something - properties or capabilities
    return return_capabilities or return_properties


def action_single_device(device_db: MqttTopic, receive_capabilities_list) -> list:
    # Get device and list with its abilities, go through all  of them and do what we know
    return_capabilities = []
    for single_capabilities in receive_capabilities_list:
        new_state = {}
        devices_capabilities = single_capabilities.get('type')
        if devices_capabilities == 'devices.capabilities.on_off':
            new_state = device_action_cap_on_off(device_db, single_capabilities.get('state'))
        return_capabilities.append({
            "type": devices_capabilities,
            "state": new_state
        })
    return return_capabilities


def parse_devices_query_or_action(dev_list: dict, command: str = 'query') -> list:
    all_device_state_answer = []
    root_device_list = dev_list.get('devices')
    if command == 'action':
        root_device_list = dev_list.get('payload').get('devices')

    for device in root_device_list:
        device_id = device['id']
        device_db = MqttTopic.objects.filter(str_id=device_id, alice=True).first()
        if not device_db:
            logger.error(f'Device {device_id} not found in DB')
            all_device_state_answer.append({
                "id": device_id,
                "error_code": "DEVICE_UNREACHABLE",
                "error_message": "Device not found in DB :("
            })
            continue

        # if device_db.alice_data.get('capabilities'):
        cap_or_prop = 'capabilities'
        if device_db.alice_data.get('properties'):
            cap_or_prop = 'properties'
        cap_or_prop_result = query_single_device_state(device_db) if command == 'query' \
            else action_single_device(device_db, device.get(cap_or_prop))

        if not cap_or_prop_result:
            logger.info("No result")
            cap_or_prop = "error_code"
            cap_or_prop_result = "DEVICE_UNREACHABLE"

        all_device_state_answer.append({
            "id": device_id,
            cap_or_prop: cap_or_prop_result
        })

    return all_device_state_answer
