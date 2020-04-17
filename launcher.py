import subprocess

subprocess.Popen(["mosquitto", "-v"])
subprocess.Popen(["python", "plotter.py"])
subprocess.Popen(["python", "producer"])
