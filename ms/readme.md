### Here are independent microservices that run separately

* *hw* - works directly with hardware, for example with ModBus via serial port, (FastAPI, asynchronous)
* *mqtt-sub* - constantly listens to MQTT and depending on what arrives there, performs certain actions
* *rc-mqtt* - listens to the RF module at 433Mhz frequency, and everything that arrives there is published in MQTT AS IS