#!/usr/bin/env python
"""MQTT client producing data."""

import json
import collections
import multiprocessing
import threading
import time
import warnings

import paho.mqtt.client as mqtt
import numpy as np

MQTTHOST = "mqtt.greyltc.com"
topic = input("Enter publication topic [data]: ")
if topic == "":
    topic = "data"
print(f"Publishing to mqtt://{MQTTHOST}/{topic}")
print("Use Ctrl-C to abort.")


class MQTTQueuePublisher(mqtt.Client):
    """MQTT client that publishes data to a topic from its own queue.

    Publishing to a topic can take a significant amount of time. If data is produced
    and quickly, appending it to a queue is faster than publishing, allowing the
    program to continue without blocking. Messages can be published from the queue
    concurrently without blocking the main program producing data.
    """

    def __init__(self):
        """Construct MQTT client, inheriting from mqtt.Client.

        Callback and connect methods are not automatically run here. They should be
        called in the same way as for the base mqtt.Client.
        """
        super().__init__()
        self._topic = None

    @property
    def topic(self):
        """Read topic attribute."""
        return self._topic

    def start_q(self, topic):
        """Start queue and mqtt client threads.

        The MQTT client publishes data to a topic from its own queue.

        topic : str
            MQTT topic to publish to.
        """
        if self._topic is None:
            self._topic = topic
            self.loop_start()  # start MQTT client thread
            self._q = collections.deque()
            self._t = threading.Thread(
                target=self._queue_publisher, args=(self._q, self._topic)
            )
            self._t.start()
        else:
            warnings.warn(
                f"A queue for '{self._topic}' is already running. End that queue first or instantiate a new queue publisher client."
            )

    def end_q(self):
        """End a thread that publishes data to a topic from its own queue."""
        self._q.appendleft("stop")  # send the queue thread a stop command
        self._t.join()  # join thread
        self.loop_stop()
        self._topic = None  # forget thread and queue

    def append_payload(self, topic, payload):
        """Append a payload to a queue.

        topic : str
            MQTT topic to publish to.
        """
        self._q.append(payload)

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
                if payload == "stop":  # return if we were asked to die
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
        print(f"\nCleaning up {self._topic}...")
        self.end_q()
        self.disconnect()
        print(f"Clean!")


class VoltageDataHandler(MQTTQueuePublisher):
    """Publish voltage vs. time data with MQTT client."""

    def __init__(self, idn=""):
        """Construct MQTT queue publisher.

        Parameters
        ----------
        idn : str
            Identity string to send with data.
        """
        super().__init__()
        self.idn = idn

    def handle_data(self, data):
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
            "id": self.idn,
        }
        # turn dict into string that mqtt can send
        payload = json.dumps(payload)
        self.append_payload(topic, payload)


class IVDataHandler(MQTTQueuePublisher):
    """Publish current vs. voltage data with MQTT client."""

    def __init__(self, idn=""):
        """Construct MQTT queue publisher.

        Parameters
        ----------
        idn : str
            Identity string to send with data.
        """
        super().__init__()
        self.idn = idn

    def handle_data(self, data):
        """Perform tasks with data.

        Parameters
        ----------
        data : array
            Array of data from exp_2.
        """
        payload = {
            "data": data.tolist(),
            "clear": False,
            "id": self.idn,
        }
        # turn dict into string that mqtt can send
        payload = json.dumps(payload)
        self.append_payload(topic, payload)


class MPPTDataHandler(MQTTQueuePublisher):
    """Publish max power point tracking data with MQTT client."""

    def __init__(self, idn=""):
        """Construct MQTT queue publisher.

        Parameters
        ----------
        idn : str
            Identity string to send with data.
        """
        super().__init__()
        self.idn = idn

    def handle_data(self, data):
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
            "id": self.idn,
        }
        payload = json.dumps(payload)
        self.append_payload(topic, payload)


class CurrentDataHandler(MQTTQueuePublisher):
    """Publish current vs. time data with MQTT client."""

    def __init__(self, idn=""):
        """Construct MQTT queue publisher.

        Parameters
        ----------
        idn : str
            Identity string to send with data.
        """
        super().__init__()
        self.idn = idn

    def handle_data(self, data):
        """Perform tasks with data.

        Parameters
        ----------
        data : list
            List of data from exp_4.
        """
        payload = {
            "x1": data[0],
            "y1": data[0],
            "clear": False,
            "id": self.idn,
        }
        # turn dict into string that mqtt can send
        payload = json.dumps(payload)
        self.append_payload(topic, payload)


class EQEDataHandler(MQTTQueuePublisher):
    """Publish EQE data with MQTT client."""

    def __init__(self, idn=""):
        """Construct MQTT queue publisher.

        Parameters
        ----------
        idn : str
            Identity string to send with data.
        """
        super().__init__()
        self.idn = idn

    def handle_data(self, data):
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
            "id": self.idn,
        }
        payload = json.dumps(payload)
        self.append_payload(topic, payload)


# class MQTTDataHandler(MQTTQueuePublisher):
#     """Handle incoming data by publishing it with MQTT client."""

#     def __init__(self, idn=""):
#         """Construct MQTT queue publisher.

#         Parameters
#         ----------
#         idn : str
#             Identity string to send with data.
#         """
#         super().__init__()
#         self.idn = idn

#     def exp1_handle_data(self, data):
#         """Perform tasks with data.

#         Parameters
#         ----------
#         data : list or str
#             List of data from exp_1.
#         """
#         payload = {
#             "x1": data[0],
#             "y1": data[0],
#             "clear": False,
#             "id": self.idn,
#         }
#         # turn dict into string that mqtt can send
#         payload = json.dumps(payload)
#         self.append_payload(topic, payload)

#     def exp2_handle_data(self, data):
#         """Perform tasks with data.

#         Parameters
#         ----------
#         data : array
#             Array of data from exp_2.
#         """
#         payload = {
#             "data": data.tolist(),
#             "clear": False,
#             "id": self.idn,
#         }
#         # turn dict into string that mqtt can send
#         payload = json.dumps(payload)
#         self.append_payload(topic, payload)

#     def exp3_handle_data(self, data):
#         """Perform tasks with data.

#         Parameters
#         ----------
#         data : list
#             List of data from exp_4.
#         """
#         payload = {
#             "x1": data[0],
#             "y1": data[1],
#             "y2": data[2],
#             "y3": data[3],
#             "clear": False,
#             "id": self.idn,
#         }
#         payload = json.dumps(payload)
#         self.append_payload(topic, payload)

#     def exp4_handle_data(self, data):
#         """Perform tasks with data.

#         Parameters
#         ----------
#         data : list
#             List of data from exp_4.
#         """
#         payload = {
#             "x1": data[0],
#             "y1": data[0],
#             "clear": False,
#             "id": self.idn,
#         }
#         # turn dict into string that mqtt can send
#         payload = json.dumps(payload)
#         self.append_payload(topic, payload)

#     def exp5_handle_data(self, data):
#         """Perform tasks with data.

#         Parameters
#         ----------
#         data : list
#             List of data from exp_4.
#         """
#         payload = {
#             "x1": data[0],
#             "y1": data[1],
#             "y2": data[2],
#             "clear": False,
#             "id": self.idn,
#         }
#         payload = json.dumps(payload)
#         self.append_payload(topic, payload)


def exp_1(n, data_handler=None):
    """Generate Type 1 data.

    Parameters
    ----------
    n : int
        Number of data points.
    data_handler : obj
        Instance of a data handler with a handle_data() method.
    """
    print("exp1")
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
    print("exp2")
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
    print("exp3")
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
    print("exp4")
    for i in range(n):
        y = 20 + (np.random.rand() - 0.5) / 3
        data = [i, y]
        # handle data if possible
        if data_handler is not None:
            data_handler(data)
        time.sleep(0.25)


def exp_5(n, data_handler=None):
    """Generate Type 5 data.

    Parameters
    ----------
    n : int
        Number of data points.
    data_handler : obj
        Instance of a data handler with a handle_data() method.
    """
    print("exp5")
    for i in range(n):
        y1 = -i + 10
        y2 = i
        data = [i, y1, y2]
        # handle data if possible
        if data_handler is not None:
            data_handler(data)
        time.sleep(0.25)


# experiment worker threads
def producer(args):
    """Simulate an experiment in a dedicated thread.

    Parameters
    ----------
    n : int
        Number of data points.
    exp : function handle
        Experiment function to call.
    mqttdh : MQTTDataHandler
        MQTT data handler object.
    data_handler : function handle
        Data handler function.
    """
    n, exp, mqttdh = args
    with mqttdh:
        for i in range(1):
            mqttdh.idn = f"dev{i}"
            exp(n, mqttdh.handle_data)
            time.sleep(5)
            d = {"clear": True, "id": f"{mqttdh.idn}"}
            d = json.dumps(d)
            mqttdh.append_payload(topic, d)
            i += 1


# number of points per graph
n = 30

subtopics = []
subtopics.append(f"{topic}/exp1")
subtopics.append(f"{topic}/exp2")
subtopics.append(f"{topic}/exp3")
subtopics.append(f"{topic}/exp4")
subtopics.append(f"{topic}/exp5")

vdh = VoltageDataHandler()
idh = IVDataHandler()
mdh = MPPTDataHandler()
cdh = CurrentDataHandler()
edh = EQEDataHandler()

dhs = [vdh, idh, mdh, cdh, edh]

for dh, st in zip(dhs, subtopics):
    dh.connect(MQTTHOST)
    dh.start_q(st)

# produce data in series
producer((n, exp_1, vdh))
producer((n, exp_2, idh))
producer((n, exp_3, mdh))
producer((n, exp_4, cdh))
producer((n, exp_5, edh))


# producers = []
# for subtopic, exp, dh in zip(subtopics, experiments, data_handlers):
#     print(subtopic)
#     dh.connect(MQTTHOST)
#     dh.start_q(subtopic)
#     _t = threading.Thread(target=producer, args=(n, exp, dh, dh.handle_data))
#     _t.start()
#     producers.append(_t)


# for t in producers:
#     t.join()
# # Produce data and publish it in context
# with mqttdh:
#     # produce data
#     while True:
#         # run experiment with a type 1 graph
#         exp_1(n, mqttdh.exp1_handle_data)

#         # signal to clear the data array
#         time.sleep(2)
#         d = {"clear": True, "type": "type2"}
#         d = json.dumps(d)
#         mqttdh.append_payload(topic, d)

#         # run experiment with a type 2 graph
#         exp_2(n, mqttdh.exp2_handle_data)

#         # signal to clear the data array
#         time.sleep(2)
#         d = {"clear": True, "type": "type3"}
#         d = json.dumps(d)
#         mqttdh.append_payload(topic, d)

#         # run experiment with a type 3 graph
#         exp_3(n, mqttdh.exp3_handle_data)

#         # signal to clear the data array
#         time.sleep(2)
#         d = {"clear": True, "type": "type4"}
#         d = json.dumps(d)
#         mqttdh.append_payload(topic, d)

#         # run experiment with a type 4 graph
#         exp_4(n, mqttdh.exp4_handle_data)

#         # signal to clear the data array
#         time.sleep(2)
#         d = {"clear": True, "type": "type1"}
#         d = json.dumps(d)
#         mqttdh.append_payload(topic, d)
