"""MQTT client producing data."""

import json
import queue
import threading
import time

import paho.mqtt.client as mqtt
import numpy as np

# MQTTHOST = "127.0.0.1"
MQTTHOST = "mqtt.greyltc.com"


def publish():
    """Read from queue and publish data using mqtt."""
    while True:
        try:
            # read data from queue
            d = q.get(timeout=3)
            q.task_done()
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
        # data for type 1 graph
        for i in range(100):
            y = 1 + (np.random.rand() - 0.5) / 3
            d = {
                "x1": i,
                "y1": y,
                "clear": False,
                "type": "type1",
                "ylabel": "voltage (V)",
            }
            # turn dict into string that mqtt can send
            d = json.dumps(d)
            # add data to queue
            q.put(d)
            time.sleep(0.25)

        # signal to clear the data array
        time.sleep(2)
        d = {"clear": True, "type": "type2"}
        d = json.dumps(d)
        q.put(d)

        # data for type 2 graph
        x1 = np.linspace(-1, 30, 100)
        x2 = x1
        y1 = -2 * x1
        y2 = -2.5 * x2
        arr = np.vstack([x1, y1, x2, y2]).T
        d = {"data": arr.tolist(), "clear": False, "type": "type2"}
        # turn dict into string that mqtt can send
        d = json.dumps(d)
        # add data to queue
        q.put(d)

        # signal to clear the data array
        time.sleep(2)
        d = {"clear": True, "type": "type3"}
        d = json.dumps(d)
        q.put(d)

        # data for type 3 graph
        for i in range(100):
            y1 = 20 + 2 * (np.random.rand() - 0.5)
            y2 = y1 + 1
            y3 = 1 + (np.random.rand() - 0.5) / 3
            d = {"x1": i, "y1": y1, "y2": y2, "y3": y3, "clear": False, "type": "type3"}
            d = json.dumps(d)
            q.put(d)
            time.sleep(0.25)

        # signal to clear the data array
        time.sleep(2)
        d = {"clear": True, "type": "type4"}
        d = json.dumps(d)
        q.put(d)

        # data for type 4 graph
        for i in range(100):
            y1 = -i + 10
            y2 = i
            d = {"x1": i, "y1": y1, "y2": y2, "clear": False, "type": "type4"}
            d = json.dumps(d)
            q.put(d)
            time.sleep(0.25)

        # signal to clear the data array
        time.sleep(2)
        d = {"clear": True, "type": "type1"}
        d = json.dumps(d)
        q.put(d)

    except KeyboardInterrupt:
        p.join()
        break

# close mqtt thread
mqttc.loop_stop()
