#!/usr/bin/env python
"""MQTT client producing data."""

import json
import queue
import threading
import time

import paho.mqtt.client as mqtt
import numpy as np

MQTTHOST = "mqtt.greyltc.com"


def publish_q_to_mqtt_client(local_q, local_mqttc):
    """Read from queue and publish data using mqtt."""
    if not local_q.empty():
        # read data from queue
        d = local_q.get(timeout=3)
        local_q.task_done()
        info = local_mqttc.publish("data", d, qos=2)
        info.wait_for_publish()

# Producer function will add data to a queue that mqtt client worker can publish. It's
# better not to let mqtt publish data immediately because it's slow and blocks the
# program. Writing to and reading from a queue is fast allowing the two steps to be
# decoupled.
q = queue.Queue()

# let's wrap the client with __enter__ and __exit__ methods
# so that we can make sure it gets cleaned up properly
class WrappedClient(mqtt.Client):
    def connect(self, *args, **kwargs):
        self._connect_args = args
        self._connect_kwargs = kwargs

    # register a thread to be cleaned up later
    def add_thread(self, thread):
        self.p = thread

    def __enter__(self):
        super(WrappedClient, self).connect(*self._connect_args, **self._connect_kwargs)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # make sure everything gets cleaned up properly
        print('\nCleaning up...')
        if 'p' in self.__dict__:
            self.p.join()  # join thread only if it was registered here
        self.loop_stop()
        self.disconnect()
        print('All clean!')

c = WrappedClient()
c.connect(MQTTHOST)  # fake connection here

# create client and connect to server
with c as mqttc: # actual connection happens in the __enter__ that gets called here
    # Create thread that reads from queue and publishes data over mqtt.
    p = threading.Thread(target=publish_q_to_mqtt_client, args=(q, mqttc, ))
    p.start()
    mqttc.add_thread(p)  # register the thread so it gets cleaned up

    # start new mqtt thread
    mqttc.loop_start()

    # Produce data
    while True:
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
