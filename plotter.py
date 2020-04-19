"""Plot data obtained from MQTT broker using Dash."""

import json

import dash
import dash_core_components as dcc
import dash_html_components as html
import numpy as np
import paho.mqtt.client as mqtt
import plotly

MQTTHOST = "127.0.0.1"
DASHHOST = "127.0.0.2"

data = np.empty((0, 2))

app = dash.Dash(__name__)
app.layout = html.Div(
    html.Div(
        [
            dcc.Graph(id="live-update-graph", animate=True),
            dcc.Interval(
                id="interval-component",
                interval=1 * 1000,  # in milliseconds
                n_intervals=0,
            ),
        ]
    )
)


@app.callback(
    dash.dependencies.Output("live-update-graph", "figure"),
    [dash.dependencies.Input("interval-component", "n_intervals")],
)
def update_graph_live(n):
    """Update graph."""
    global data

    trace = {"x": data[:, 0], "y": data[:, 1], "type": "scatter"}

    layout = {
        "xaxis": {"title": "time (s)"},
        "yaxis": {"title": "y (s^2)"},
    }

    if len(data[:, 0]) != 0:
        layout["xaxis"]["range"] = [int(min(data[:, 0])) - 1, int(max(data[:, 0])) + 1]
        layout["yaxis"]["range"] = [int(min(data[:, 1])) - 1, int(max(data[:, 1])) + 1]

    return plotly.graph_objs.Figure(data=[trace], layout=layout)


def on_message(mqttc, obj, msg):
    """Act on an MQTT msg.

    Append or clear data.
    """
    global data
    d = json.loads(msg.payload)
    if d["clear"] is True:
        data = np.empty((0, 2))
    else:
        data = np.append(data, np.array([[d["x"], d["y"]]]), axis=0)


# create client and connect to server
mqttc = mqtt.Client()
mqttc.on_message = on_message
mqttc.connect(MQTTHOST)
mqttc.subscribe("data", qos=2)

# start new thread for mqtt client
mqttc.loop_start()

# start dash server
app.run_server(host=DASHHOST, debug=True)

# stop mqtt thread
mqttc.loop_stop()
