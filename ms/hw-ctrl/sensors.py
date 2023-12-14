# -*- coding: utf-8 -*-
__author__ = 'Nikolay Mamashin (mamashin@gmail.com)'

import asyncio
from lruttl import LRUCache
from pathlib import Path
from fastapi import FastAPI, Response, status
from typing import Union
from loguru import logger
from decouple import config # noqa
from aiofile import LineReader, AIOFile
from os.path import exists as file_exist
from smbus2_asyncio import SMBus2Asyncio

cache = LRUCache(64)  # 10 - глубина кэша


def format_result(res: dict) -> dict:
    result = {'error': res.get('error', False)}
    res.pop('error', None)
    result['data'] = res
    return result


async def sensor_sht3x(dh31_addr: int = 0x44, request_type: str = 'temp'):
    """
    Read data from light sensor SHT3x (Temp + Humidity)
    Address 0x44 (or 0x45)
    """
    result = {'error': True}

    cache_result_temp = cache.get('sht3x_temp')
    if cache_result_temp and request_type == 'temp':
        return format_result(cache_result_temp)
    cache_result_hum = cache.get('sht3x_humidity')
    if cache_result_hum and request_type != 'temp':
        return format_result(cache_result_hum)

    if cache.get('sensor_sht3x_lock'):  # block for flood requests
        return result
    cache.set('sensor_sht3x_lock', True, 1)

    bus = SMBus2Asyncio(1)
    await bus.open()
    try:
        await bus.write_i2c_block_data(dh31_addr, 0x2C, [0x06])  # read LOW resolution 2 words (for speed)
    except Exception as e:
        logger.error(f'Failed to open DH31x sensor - {e}')
        return result
    await asyncio.sleep(0.5)
    raw_data = await bus.read_i2c_block_data(dh31_addr, 0x00, 6)
    temp_raw = (raw_data[0] << 8 | raw_data[1])
    humidity_raw = (raw_data[3] << 8 | raw_data[4])
    temp = -45 + (175 * temp_raw / 65535.0)
    humidity = 100 * humidity_raw / 65535.0
    cache.set('sht3x_temp', {'value': float(f'{temp:.1f}'), 'instance': 'temperature', 'error': False}, 60)
    cache.set('sht3x_humidity', {'value': int(humidity), 'instance': 'humidity', 'error': False}, 60)

    if request_type != 'temp':
        return format_result(cache.get('sht3x_humidity'))

    return format_result(cache.get('sht3x_temp'))


async def sensor_light():
    """
    Read data from light sensor BH 1750
    """
    result = {'error': True}
    if cache.get('sensor_light_lock'):  # block for flood requests
        return result
    if cache_result := cache.get('light_result'):
        return format_result(cache_result)

    cache.set('sensor_light_lock', True, 1)
    light_address = 0x23
    bus = SMBus2Asyncio(1)
    await bus.open()
    try:

        await bus.read_i2c_block_data(light_address, 0x23, 2)  # read LOW resolution 2 words (for speed)
    except Exception as e:
        logger.error(f'Failed to open light sensor - {e}')
        return result
    await asyncio.sleep(0.1)
    raw_data = await bus.read_i2c_block_data(light_address, 0x23, 2)
    lux = (raw_data[0] << 8 | raw_data[1]) / 1.2
    result['value'] = float(f'{lux:.1f}')
    result['instance'] = "illumination"
    result['error'] = False

    cache.set('light_result', result.copy(), 30)  # На 30 секунд кешируем результат

    return format_result(result)
