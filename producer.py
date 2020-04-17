"""MQTT client producing data."""

import json

# import context  # Ensures paho is in PYTHONPATH
import paho.mqtt.client as mqtt
import time

host = "127.0.0.1"

# create client and connect to server
mqttc = mqtt.Client()
mqttc.connect(host)
mqttc.loop_start()

tstart = time.time()
while True:
    t = time.time() - tstart
    y = t ** 2 - 10
    d = {"x": t, "y": y}
    d = json.dumps(d)
    info = mqttc.publish("data", d, qos=2)
    info.wait_for_publish()
    time.sleep(1)
