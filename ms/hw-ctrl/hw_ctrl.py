# -*- coding: utf-8 -*-
__author__ = 'Nikolay Mamashin (mamashin@gmail.com)'

import asyncio
from pathlib import Path
from fastapi import FastAPI, Response, status
from typing import Union
from serial_asyncio import create_serial_connection
from pymodbus.client.asynchronous.async_io import ModbusClientProtocol
from pymodbus.transaction import ModbusRtuFramer
from pymodbus.factory import ClientDecoder
from loguru import logger
from decouple import config # noqa
from aiofile import LineReader, AIOFile
from os.path import exists as file_exist
from smbus2_asyncio import SMBus2Asyncio
from sensors import sensor_sht3x, sensor_light

BASE_DIR = Path(__file__).resolve(strict=True).parent
logger.remove()
logger.add(f"{BASE_DIR}/hw_ctrl.log")

descr = """
## Working with Modbus via API

#### * `unit_id` Modbus Unit ID. Number in decimal format
#### * `channel` Relay channel number or input (input), starts from 1
#### * `cmd` Command. Can be on|off|toggle|status
"""

app = FastAPI(description=descr)
DEBUG = config('DEBUG', default=False, cast=bool)


def format_result(res: dict) -> dict:
    result = {'error': res['error']}
    res.pop('error', None)
    result['data'] = res
    return result


async def modbus_pzem(client: ModbusClientProtocol):
    result = {'error': True}
    try:
        read_register = await client.read_input_registers(0, 8, unit=5)
        if read_register.isError():
            return result
        data = {
            'voltage': float(f"{read_register.registers[0] * 0.01:.2f}"),
            'amp': float(f"{read_register.registers[1] * 0.01:.2f}"),
            'power': float(f"{((read_register.registers[3] << 16) | read_register.registers[2]) * 0.1:.1f}"),
            'energy': (read_register.registers[5] << 16) | read_register.registers[4],
            'raw_value': read_register.registers
        }
        result['error'] = False
        result['data'] = data
        return result
    except Exception as e:
        logger.error(e)
        return result


async def modbus(client: ModbusClientProtocol, unit_id: int = 1, channel: int = 1, cmd_type: str = 'read',
                 cmd_set: str = 'on'):
    result = {'error': True}
    if cmd_type == 'read' or cmd_set == 'status':
        try:
            read_register = await client.read_holding_registers(channel, 1, unit=unit_id)
            if read_register.isError():
                return result
            result['status'] = read_register.registers[0]
            result['error'] = False
            return result
        except Exception as e:
            logger.error(e)
            return result

    if cmd_type == 'write':
        base_reg = 256
        if cmd_set == 'off':
            base_reg = 512
        if cmd_set == 'toggle':
            base_reg = 768
        try:
            write_register = await client.write_register(channel, base_reg, unit=unit_id)
            if write_register.isError():
                return result
            await asyncio.sleep(0.1)
            read_register = await client.read_holding_registers(channel, 1, unit=unit_id)
            if read_register.isError():
                return result
        except Exception as e:
            logger.error(e)
            return result

        result['status'] = read_register.registers[0]
        result['error'] = False
        return result


def make_protocol():
    return ModbusClientProtocol(framer=ModbusRtuFramer(ClientDecoder()), timeout=0.7) # noqa


async def serial(unit_id: int = 1, channel: int = 1, cmd_type: str = 'read', cmd_set: Union[str, None] = None):
    result = []
    stop_bits = 1
    loop = asyncio.get_event_loop()
    if cmd_type == 'pzem':
        stop_bits = 2
    serial_coro, protocol = await create_serial_connection(loop,  make_protocol, config('MODBUS_SERIAL'), baudrate=9600,
                                                           stopbits=stop_bits, timeout=0.1)
    if cmd_type == 'pzem':
        modbus_cmd = asyncio.create_task(modbus_pzem(protocol))
    else:
        modbus_cmd = asyncio.create_task(modbus(protocol, unit_id, channel, cmd_type, cmd_set))

    done, pending = await asyncio.wait({modbus_cmd})
    if modbus_cmd in done:
        result = modbus_cmd.result()
    serial_coro.close()

    return result


@app.get("/relay/{unit_id}/{channel}")
async def relay_on_off(unit_id: int, channel: Union[int, str], cmd: Union[str, None] = None):
    """
    :param unit_id: ModBus Unit ID
    :param channel: Номер реле
    :param cmd: on|off|toggle
    :return:
     {
        "error": false,
        "data": {
            "status": 1,
            "channel": 1
                }
    }
    """
    if DEBUG:
        logger.info(f'{unit_id=}, {channel=}, {cmd=}')
    result = {}
    cmd_type = 'read'
    if cmd:
        cmd_type = 'write'
    serial_open = asyncio.create_task(serial(unit_id, channel, cmd_type, cmd))
    done, pending = await asyncio.wait({serial_open})
    await asyncio.sleep(0.1)
    if serial_open in done:
        result = serial_open.result()
    if not result['error']:
        result['channel'] = channel
        result['unit_id'] = unit_id

    return format_result(result)


@app.get("/input/{unit_id}/{channel}")
async def input_read(unit_id: int, channel: int):
    result = {}
    cmd_type = 'read'
    if DEBUG:
        logger.info(f'Input - {unit_id=}, {channel=}')
    serial_open = asyncio.create_task(serial(unit_id, channel + 128, cmd_type))
    done, pending = await asyncio.wait({serial_open})
    await asyncio.sleep(0.1)
    if serial_open in done:
        result = serial_open.result()
    if not result['error']:
        result['channel'] = channel
        result['unit_id'] = unit_id

    return format_result(result)


@app.get("/pzem")
async def read_pzem():
    """
    :return:
    {
    "error": false,
        "data": {
            "voltage": 11.88,
            "amp": 0.63,
            "power": 7.4,
            "energy": 81}
    }
    """
    result = {}
    serial_open = asyncio.create_task(serial(config('PZEM_UNIT_ID'), 1, 'pzem'))
    done, pending = await asyncio.wait({serial_open})
    if serial_open in done:
        result = serial_open.result()
    return result


@app.get("/w1/{device_id}")
async def wire1_read(device_id: str):
    """ Read 1Wire Dallas temp
    {
      "error": false,
      "data": {
        "device_id": "28-xxx",
        "value": "25.7",
        "instance": "temperature"
      }
    } """
    result = {'error': True}
    cnt = 1
    if DEBUG:
        logger.info(f"W1 Get request {device_id}")
    # async with AIOFile(f"/tmp/mytemp", 'r') as f:
    """
    Wire1 info file looks like:
     #cat /sys/bus/w1/devices/28-0215635abeff/w1_slave 
     9e 01 4b 46 7f ff 0c 10 8a : crc=8a YES
     9e 01 4b 46 7f ff 0c 10 8a t=25875
    """
    w1_file_path = f"/sys/bus/w1/devices/{device_id}/w1_slave"
    if not file_exist(w1_file_path):
        logger.error(f"w1 device not found - {device_id}")
        return format_result(result)
    async with AIOFile(w1_file_path, 'r') as f:
        async for line in LineReader(f):
            if cnt == 1 and not str(line).strip().endswith("YES"):
                logger.error(f"File temp info is corrupt - {str(line)}")
                break
            if cnt == 2:
                try:
                    ll = str(line)
                    temp = int(ll[ll.find('t=') + 2:])
                    # result['device_id'] = device_id
                    result['value'] = float(f'{temp/1000:.1f}')
                    result['instance'] = "temperature"
                    result['error'] = False
                except Exception as e:
                    logger.error(f"Error to convert temp - {e}")
                    break
            cnt += 1
            if cnt >= 3:
                break
    return format_result(result)


@app.get("/sensor/{sensor_type}")
async def sensor_request(sensor_type: str):
    result = {'error': True}
    if 'sht3x_humidity' in sensor_type:
        return await sensor_sht3x(request_type='humidity')
    if 'sht3x_temp' in sensor_type:
        return await sensor_sht3x(request_type='temp')
    if 'light' in sensor_type:
        return await sensor_light()
    return result


@app.on_event("startup")
async def startup_event():
    pass

# import ctypes as ct
# ct.c_int16(4995).value / 100
