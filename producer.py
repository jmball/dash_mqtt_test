"""MQTT client producing data."""

import json
import queue
import threading
import time

import paho.mqtt.client as mqtt


MQTTHOST = "127.0.0.1"


def publish():
    """Read from queue and publish data using mqtt."""
    while True:
        try:
            # read data from queue
            d = q.get(timeout=2)
            info = mqttc.publish("data", d, qos=2)
            info.wait_for_publish()
        except queue.Empty:
            break


# Producer function will add data to a queue that mqtt client worker can publish. It's
# better not to let mqtt publish data immediately because it's slow and blocks the
# program. Writing to and reading from a queue is fast allowing the two steps to be
# decoupled.
q = queue.Queue()

# Create thread that reads from queue and publishes data over mqtt.
p = threading.Thread(target=publish)
p.start()

# create client and connect to server
mqttc = mqtt.Client()
mqttc.connect(MQTTHOST)

# start new mqtt thread
mqttc.loop_start()

# Produce data
while True:
    try:
        for i in range(20):
            y = i ** 2
            d = {"x": i, "y": y, "clear": False}
            # turn dict into string that mqtt can send
            d = json.dumps(d)
            # add data to queue
            q.put(d)
            time.sleep(1)

        # signal to clear the data array
        d = {"clear": True}
        d = json.dumps(d)
        q.put(d)
        time.sleep(1)

        for i in range(20):
            y = -2 * i + 10
            d = {"x": i, "y": y, "clear": False}
            d = json.dumps(d)
            q.put(d)
            time.sleep(1)

        d = {"clear": True}
        d = json.dumps(d)
        q.put(d)
        time.sleep(1)
    except KeyboardInterrupt:
        break

# close mqtt thread
mqttc.loop_stop()
