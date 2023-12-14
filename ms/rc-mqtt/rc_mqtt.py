# -*- coding: utf-8 -*-

__author__ = 'Nikolai Mamashin (mamashin@gmail.com)'

from lruttl import LRUCache
import paho.mqtt.publish as publish
import time
import sys
import signal
import json
from loguru import logger
from rpi_rf import RFDevice
from decouple import config # noqa

logger.remove()
logger.add(sys.stderr, format="{level} | {message}")

DEBUG = config('RC_DEBUG', default=False, cast=bool)
cache = LRUCache(10)  # 10 - cache depth
rf_device = RFDevice(27)  # 27 - the GPIO number used RF receiver


def send_to_mqtt(code):
    if cache.get(code):
        if DEBUG:
            logger.debug(f"Code '{code}' already in cache")
        return
    cache.set(code, True, 2)  # cache TTL time
    if DEBUG:
        logger.debug(f"Send code {code} to MQTT")
    publish.single("rc_code", json.dumps({"data": code}).encode())


def exit_handler(signal, frame):
    rf_device.cleanup()
    logger.info("Exit. Bye-Bye.")
    sys.exit(0)


def rx_read():
    rf_device.enable_rx()
    timestamp = None
    while True:
        if rf_device.rx_code_timestamp != timestamp:
            timestamp = rf_device.rx_code_timestamp
            if DEBUG:
                logger.debug(f"{rf_device.rx_code=} {rf_device.rx_pulselength=}")
            if rf_device.rx_pulselength < 500 and len(str(rf_device.rx_code)) > 5:  # simple noise filter
                send_to_mqtt(rf_device.rx_code)
        time.sleep(0.1)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, exit_handler)
    logger.info("Start RC to MQTT service")
    rx_read()
