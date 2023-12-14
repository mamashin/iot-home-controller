## IoT Home Controller

This project is a Python-based Internet of Things (IoT) application. It started as a hobby project for home automation system that uses a Raspberry Pi as a gateway. The Raspberry Pi is connected to a 433Mhz RF module and a USB-to-serial RS-485 adapter. The RF module is used to control RF-based devices, such as remote switch buttons. RS-485 adapter is used to control ModBus-based devices.

### The main work flow when I switch ON/OFF lamp via a remote switch:

1. The RF module (connected to RPi) receives a signal from a remote switch (microservice [rc-mqtt](ms/rc-mqtt/rc_mqtt.py)) and publishes the signal in MQTT with topic "rc_code" and RC code as the payload (e.g. `{"rc_code": 12345678}`).
2. The MQTT subscriber (microservice [mqtt-sub](ms/mqtt-sub/mqtt_sub.py)) receives all messages (not only from `rc-mqtt`) and post them to the Django via API.
3. The Django get raw message from `mqtt-sub`, parse it, and if found a match, it will perform an action and send command to last microservice [hw-ctrl](ms/hw-ctrl/hw_ctrl.py). Example, if we turn ON kitchen lamp, Django found record like *0123456789* (RC code) is relay number 1 and unit number 2 (kitchen lamp connected) and make http request `/relay/1/1/?cmd=on` to `hw-ctrl`.
4. The `hw-ctrl` microservice receives the request, parse it and send command to the relay (if it commands to relay) via ModBus protocol. Now service `hw-ctrl` is able to control the relay (set in get state) and some type of sensors (get state).

![scheme.jpeg](images%2Fscheme.jpeg)

Commands from RC switches - its only one way to control devices. You can send commands directly to MQTT, example it can be web interface like [Node-RED](https://nodered.org/) or [Home Assistant](https://www.home-assistant.io/). I added support for [Alice assistant (Yandex)](https://yandex.ru/alice) and you can control devices via voice commands (its really cool).

A little bit about hardware. As I said, the heart of the system is Raspberry Pi. Important part of project is relay, I use chipper relay boards from AliExpress like this:

[16-Channel 12V 10A Board RS485 Modbus RTU Relay Module](https://aliexpress.ru/item/4000834191354.htm)

![relay.jpeg](images%2Frelay.jpeg)

[16 Input 16 Output RS485 Board Modbus RTU Module](https://aliexpress.ru/item/1005003367166902.html)

![input_relay.jpeg](images%2Finput_relay.jpeg)

Remote switches - I use 433Mhz transmitter:

[433MHz Universal Wireless Remote Control Wall Panel RF Transmitter](https://aliexpress.ru/item/32956646243.html)

![rc.png](images%2Frc.png)


Beside ModBus devices service support some type of sensors, like  DS18B20, BH1750, BME280, BMP280 & etc., connected via I2C or Wire1 bus, support devices you can see at [hw_ctrl.py](ms/hw-ctrl/hw_ctrl.py). I use sensors for monitoring temperature, humidity, light, etc. 

![rpi.jpeg](images%2Frpi.jpeg)

![total_view.jpeg](images%2Ftotal_view.jpeg)
