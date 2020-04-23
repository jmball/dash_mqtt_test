#!/usr/bin/env python
"""MQTT client producing data."""

import json
import collections
import threading
import time

import paho.mqtt.client as mqtt
import numpy as np

MQTTHOST = "mqtt.greyltc.com"
topic = input("Enter publication topic [data]: ")
if topic == "":
    topic = "data"
print(f"Publishing to mqtt://{MQTTHOST}/{topic}")
print("Use Ctrl-C to abort.")


class MQTTQueuePublisher(mqtt.Client):
    """MQTT client that publishes data from its own queue."""

    def __init__(self, host):
        """Init MQTT queue publisher client, inheriting from MQTT client.

        Parameters
        ----------
        host : str
            MQTT broker host name.
        """
        super().__init__()
        self.connect(host)
        self.loop_start()
        self.qs = {}  # dictionary of quques labelled by topic

    def start_q(self, topic):
        """Start a thread that publishes data from the queue on a topic.

        topic : str
            MQTT topic to publish to.
        """
        q = collections.deque()
        t = threading.Thread(target=self._queue_publisher, args=(q, topic))
        t.start()
        self.qs[topic] = {"q": q, "t": t}

    def _queue_publisher(self, q, topic):
        """Publish elements in the queue.

        q : deque
            Deque to publish to.
        topic : str
            MQTT topic to publish to.
        """
        while True:
            if len(q) > 0:
                # read data from queue
                d = q.popleft()
                if d == "die":  # return if we were asked to die
                    break
                info = self.publish(topic, d, qos=2)
                info.wait_for_publish()

    def __enter__(self):
        """Enter the runtime context related to this object."""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Exit the runtime context related to this object.

        Make sure everything gets cleaned up properly.
        """
        print("\nCleaning up...")
        for d in self.qs.values():
            d["q"].appendleft("die")  # send the queue thread a kill command
            d["t"].join()  # join thread
        self.loop_stop()
        self.disconnect()
        print("All clean!")


class MQTTDataHandler(MQTTQueuePublisher):
    """Handle incoming data by publishing it with MQTT client."""

    def __init__(self, host):
        """Construct MQTT queue publisher.

        Parameters
        ----------
        host : str
            MQTT broker host name.
        """
        super().__init__(host)

    def handle_data(self, data):
        """Perform tasks with data.

        Parameters
        ----------
        data : JSON str
            JSON-ified data string
        """
        self.qs[topic]["q"].append(data)


def exp_1(n, data_handler=None):
    """Generate Type 1 data.

    Parameters
    ----------
    n : int
        Number of data points.
    data_handler : obj
        Instance of a data handler with a handle_data() method.
    """
    for i in range(n):
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
        # handle data if possible
        if hasattr(data_handler, "handle_data"):
            data_handler.handle_data(d)
        time.sleep(0.25)


def exp_2(n, data_handler=None):
    """Generate Type 2 data.

    Parameters
    ----------
    n : int
        Number of data points.
    data_handler : obj
        Instance of a data handler with a handle_data() method.
    """
    x1 = np.linspace(-1, 30, n)
    x2 = x1
    y1 = -2 * x1
    y2 = -2.5 * x2
    arr = np.vstack([x1, y1, x2, y2]).T
    d = {"data": arr.tolist(), "clear": False, "type": "type2"}
    # turn dict into string that mqtt can send
    d = json.dumps(d)
    # handle data if possible
    if hasattr(data_handler, "handle_data"):
        data_handler.handle_data(d)


def exp_3(n, data_handler=None):
    """Generate Type 3 data.

    Parameters
    ----------
    n : int
        Number of data points.
    data_handler : obj
        Instance of a data handler with a handle_data() method.
    """
    for i in range(n):
        y1 = 20 + 2 * (np.random.rand() - 0.5)
        y2 = y1 + 1
        y3 = 1 + (np.random.rand() - 0.5) / 3
        d = {"x1": i, "y1": y1, "y2": y2, "y3": y3, "clear": False, "type": "type3"}
        d = json.dumps(d)
        # handle data if possible
        if hasattr(data_handler, "handle_data"):
            data_handler.handle_data(d)
        time.sleep(0.25)


def exp_4(n, data_handler=None):
    """Generate Type 4 data.

    Parameters
    ----------
    n : int
        Number of data points.
    data_handler : obj
        Instance of a data handler with a handle_data() method.
    """
    for i in range(n):
        y1 = -i + 10
        y2 = i
        d = {"x1": i, "y1": y1, "y2": y2, "clear": False, "type": "type4"}
        d = json.dumps(d)
        # handle data if possible
        if hasattr(data_handler, "handle_data"):
            data_handler.handle_data(d)
        time.sleep(0.25)


# create MQTT publisher client
mqttdh = MQTTDataHandler(MQTTHOST)
mqttdh.start_q(topic)  # start queue for topic

# number of points per graph
n = 30

# Produce data and publish it in context
with mqttdh:
    # produce data
    while True:
        # run experiment with a type 1 graph
        exp_1(n, mqttdh)

        # signal to clear the data array
        time.sleep(2)
        d = {"clear": True, "type": "type2"}
        d = json.dumps(d)
        mqttdh.qs[topic]["q"].append(d)

        # run experiment with a type 2 graph
        exp_2(n, mqttdh)

        # signal to clear the data array
        time.sleep(2)
        d = {"clear": True, "type": "type3"}
        d = json.dumps(d)
        mqttdh.qs[topic]["q"].append(d)

        # run experiment with a type 3 graph
        exp_3(n, mqttdh)

        # signal to clear the data array
        time.sleep(2)
        d = {"clear": True, "type": "type4"}
        d = json.dumps(d)
        mqttdh.qs[topic]["q"].append(d)

        # run experiment with a type 4 graph
        exp_4(n, mqttdh)

        # signal to clear the data array
        time.sleep(2)
        d = {"clear": True, "type": "type1"}
        d = json.dumps(d)
        mqttdh.qs[topic]["q"].append(d)
