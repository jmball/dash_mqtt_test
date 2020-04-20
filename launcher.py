"""Launch MQTT broker, data producer, and plotter."""

import subprocess
import time

# assumes mosquitto is the mqtt broker and has been added to path environment variable
p1 = subprocess.Popen(["mosquitto"])
p2 = subprocess.Popen(["python", "plotter.py"])
# wait some time for Flask server to load
time.sleep(5)
p3 = subprocess.Popen(["python", "producer.py"])

# end all processes with keyboard interrupt
try:
    p1.wait()
    p2.wait()
    p3.wait()
except KeyboardInterrupt:
    p1.terminate()
    p2.terminate()
    p3.terminate()
