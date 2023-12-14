# -*- coding: utf-8 -*-
__author__ = 'Nikolay Mamashin (mamashin@gmail.com)'

import signal
import asyncio
import sys
from asyncio_mqtt import Client, MqttError
import httpx
from loguru import logger
import json
from decouple import config  # noqa

DEBUG = config('MQTT_DEBUG', default=False, cast=bool)
STOP = asyncio.Event()

logger.remove()
logger.add(sys.stderr, format="{level} | {message}")


async def mqtt_publish(topic, payload):
    try:
        async with Client(config("MQTT_HOST"), clean_session=True, client_id="My_IoT_Publish") as client:
            await client.publish(topic, payload=json.dumps(payload).encode())
    except Exception as e:
        logger.error(f"Error publish to MQTT - {e}")


async def post_raw_mqtt(topic, payload) -> dict:
    result = {}
    post_data = {'topic': topic, 'payload': payload}
    async with httpx.AsyncClient() as client:
        try:
            http_response = await client.post(f'{config("MQTT_API_BASE_URL")}/rawmqtt/', data=post_data,
                                              headers={'Connection': 'close'})
        except Exception as e:
            logger.error(f'Unable post raw mqtt to {config("MQTT_API_BASE_URL")} - {e}')
            return result
        if http_response.status_code != 200:
            logger.warning(f"Post result error - '{http_response.text}'")
            return result
        response_json = http_response.json()
        if DEBUG:
            logger.info(f'Response from MQTT-DB - {response_json}')
        return response_json


async def mqtt_sub():
    logger.info(f'Ready to listen topics from mqtt broker - {config("MQTT_HOST")}')
    async with Client(config("MQTT_HOST"), clean_session=True, client_id="My_IoT_Subscribe") as client:
        async with client.unfiltered_messages() as messages:  # Receive all messages
            await client.subscribe("#")  # Tell the server to send me all messages
            async for message in messages:
                if DEBUG:
                    logger.info(f"{message.topic} - {message.payload}")

                if message.topic == "rc_code":  # Если это команда с RC (пульта) переключаемся на отдельный обработчик
                    await post_raw_mqtt(message.topic, message.payload.decode())
                    continue

                try:
                    payload_json = json.loads(message.payload.decode())
                except Exception as e:
                    logger.error(f'Cant parse payload to json - {message.payload.decode()} ({e}')
                    continue
                if payload_json.get('cmd'):
                    await post_raw_mqtt(message.topic, message.payload.decode())


def sig_int(*args):
    STOP.set()
    asyncio.get_event_loop().stop()
    sys.exit()


async def main_task():
    reconnect_interval = 30  # [seconds]
    while True:
        try:
            await mqtt_sub()
        except MqttError as error:
            logger.error(f'Error "{error}". Reconnecting in {reconnect_interval} seconds.')
        finally:
            await asyncio.sleep(reconnect_interval)


# asyncio.run(main())
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.add_signal_handler(signal.SIGINT, sig_int)
    loop.add_signal_handler(signal.SIGTERM, sig_int)
    loop.run_until_complete(main_task())
