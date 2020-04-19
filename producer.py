"""MQTT client producing data."""

import json

# import context  # Ensures paho is in PYTHONPATH
import paho.mqtt.client as mqtt
import time

host = "127.0.0.1"

# create client and connect to server
mqttc = mqtt.Client()
mqttc.connect(host)

# start new mqtt thread
mqttc.loop_start()

tstart = time.time()
loop = True
while loop:
    try:
        t = time.time() - tstart
        if t > 20:
            # clear every 20s
            d = {"clear": True}
            tstart = time.time()
        else:
            y = t ** 2 - 10
            d = {"x": t, "y": y, "clear": False}
        d = json.dumps(d)
        info = mqttc.publish("data", d, qos=2)
        info.wait_for_publish()
        time.sleep(1)
    except KeyboardInterrupt:
        loop = False

# close mqtt thread
mqttc.loop_stop()
