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
    """MQTT client that publishes data from its own queues.

    Each queue works in its own thread, one per topic, allowing concurrent appends.
    However, they all publish from the same single MQTT client thread. If publishing
    becomes rate limiting, multiple instances of this class should be used instead,
    one per topic if required.
    """

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
        self._qs = {}  # dictionary of quques labelled by topic

    def start_q(self, topic):
        """Start a thread that publishes data to a topic from its own queue.

        topic : str
            MQTT topic to publish to.
        """
        q = collections.deque()
        t = threading.Thread(target=self._queue_publisher, args=(q, topic))
        t.start()
        self._qs[topic] = {"q": q, "t": t}

    def end_q(self, topic):
        """End a thread that publishes data to a topic from its own queue.

        topic : str
            MQTT topic to publish to.
        """
        self._qs[topic]["q"].appendleft("die")  # send the queue thread a kill command
        self._qs[topic]["t"].join()  # join thread
        self._qs.pop(topic)  # forget thread and queue

    def append_payload(self, topic, payload):
        """Append a payload to a queue.

        topic : str
            MQTT topic to publish to.
        """
        self._qs[topic]["q"].append(payload)

    def _queue_publisher(self, q, topic):
        """Publish elements in the queue.

        q : deque
            Deque to publish from.
        topic : str
            MQTT topic to publish to.
        """
        while True:
            if len(q) > 0:
                # read data from queue
                payload = q.popleft()
                if payload == "die":  # return if we were asked to die
                    break
                # publish paylod with blocking wait for completion
                self.publish(topic, payload, qos=2).wait_for_publish()

    def __enter__(self):
        """Enter the runtime context related to this object."""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Exit the runtime context related to this object.

        Make sure everything gets cleaned up properly.
        """
        print("\nCleaning up...")
        for topic in self._qs.keys():
            self._qs[topic]["q"].appendleft(
                "die"
            )  # send the queue thread a kill command
            self._qs[topic]["t"].join()  # join thread
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

    def exp1_handle_data(self, data):
        """Perform tasks with data.

        Parameters
        ----------
        data : list or str
            List of data from exp_1.
        """
        payload = {
            "x1": data[0],
            "y1": data[0],
            "clear": False,
            "type": "type1",
            "ylabel": "voltage (V)",
        }
        # turn dict into string that mqtt can send
        payload = json.dumps(payload)
        self.append_payload(topic, payload)

    def exp2_handle_data(self, data):
        """Perform tasks with data.

        Parameters
        ----------
        data : array
            Array of data from exp_2.
        """
        payload = {"data": data.tolist(), "clear": False, "type": "type2"}
        # turn dict into string that mqtt can send
        payload = json.dumps(payload)
        self.append_payload(topic, payload)

    def exp3_handle_data(self, data):
        """Perform tasks with data.

        Parameters
        ----------
        data : list
            List of data from exp_4.
        """
        payload = {
            "x1": data[0],
            "y1": data[1],
            "y2": data[2],
            "y3": data[3],
            "clear": False,
            "type": "type3",
        }
        payload = json.dumps(payload)
        self.append_payload(topic, payload)

    def exp4_handle_data(self, data):
        """Perform tasks with data.

        Parameters
        ----------
        data : list
            List of data from exp_4.
        """
        payload = {
            "x1": data[0],
            "y1": data[1],
            "y2": data[2],
            "clear": False,
            "type": "type4",
        }
        payload = json.dumps(payload)
        self.append_payload(topic, payload)


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
        data = [i, y]
        # handle data if possible
        if data_handler is not None:
            data_handler(data)
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
    data = np.vstack([x1, y1, x2, y2]).T
    # handle data if possible
    if data_handler is not None:
        data_handler(data)


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
        data = [i, y1, y2, y3]
        # handle data if possible
        if data_handler is not None:
            data_handler(data)
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
        data = [i, y1, y2]
        # handle data if possible
        if data_handler is not None:
            data_handler(data)
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
        exp_1(n, mqttdh.exp1_handle_data)

        # signal to clear the data array
        time.sleep(2)
        d = {"clear": True, "type": "type2"}
        d = json.dumps(d)
        mqttdh.append_payload(topic, d)

        # run experiment with a type 2 graph
        exp_2(n, mqttdh.exp2_handle_data)

        # signal to clear the data array
        time.sleep(2)
        d = {"clear": True, "type": "type3"}
        d = json.dumps(d)
        mqttdh.append_payload(topic, d)

        # run experiment with a type 3 graph
        exp_3(n, mqttdh.exp3_handle_data)

        # signal to clear the data array
        time.sleep(2)
        d = {"clear": True, "type": "type4"}
        d = json.dumps(d)
        mqttdh.append_payload(topic, d)

        # run experiment with a type 4 graph
        exp_4(n, mqttdh.exp4_handle_data)

        # signal to clear the data array
        time.sleep(2)
        d = {"clear": True, "type": "type1"}
        d = json.dumps(d)
        mqttdh.append_payload(topic, d)
