"""Plot data obtained from MQTT broker using Dash."""

import json

import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import numpy as np
import paho.mqtt.client as mqtt
import plotly

host = "127.0.0.1"

data = np.array([[0, 0]])

app = dash.Dash(__name__)
app.layout = html.Div(
    html.Div(
        [
            dcc.Graph(id="live-update-graph"),
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

    # Create the graph with subplots
    fig = plotly.subplots.make_subplots(rows=1, cols=1)
    fig.append_trace(
        {
            "x": data[:, 0],
            "y": data[:, 1],
            "name": "data",
            "mode": "lines+markers",
            "type": "scatter",
        },
        1,
        1,
    )

    return fig


def on_message(mqttc, obj, msg):
    """Act on an MQTT msg.

    Append or clear data.
    """
    global data
    d = json.loads(msg.payload)
    if msg.payload == "clear":
        data = np.array([[0, 0]])
    else:
        data = np.append(data, np.array([[d["x"], d["y"]]]), axis=0)


# create client and connect to server
mqttc = mqtt.Client()
mqttc.on_message = on_message
mqttc.connect(host)
mqttc.subscribe("data", qos=2)

# start new thread for mqtt client
mqttc.loop_start()

# start dash server
app.run_server(host="127.0.0.2", debug=True, use_reloader=False)

# stop mqtt thread
mqttc.loop_stop()
