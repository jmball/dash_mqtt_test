"""Launch MQTT broker, data producer, and plotter."""

import subprocess
import time

# open dash plotter
p1 = subprocess.Popen(["python", "plotter.py"])
# wait some time for Flask server to load
time.sleep(10)

# start producers
p2 = subprocess.Popen(["python", "producer.py", "-m", "2", "-e", "1"])
p3 = subprocess.Popen(["python", "producer.py", "-m", "2", "-e", "2"])
p4 = subprocess.Popen(["python", "producer.py", "-m", "2", "-e", "3"])
p5 = subprocess.Popen(["python", "producer.py", "-m", "2", "-e", "4"])
p6 = subprocess.Popen(["python", "producer.py", "-m", "2", "-e", "5"])

# end all processes with keyboard interrupt
try:
    p1.wait()
    p2.wait()
    p3.wait()
    p4.wait()
    p5.wait()
    p6.wait()
except KeyboardInterrupt:
    p1.terminate()
    p2.terminate()
    p3.terminate()
    p4.terminate()
    p5.terminate()
    p6.terminate()
