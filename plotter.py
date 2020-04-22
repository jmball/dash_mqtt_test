#!/usr/bin/env python
"""Plot data obtained from MQTT broker using Dash."""

import json

import dash
import dash_core_components as dcc
import dash_html_components as html
import numpy as np
import paho.mqtt.client as mqtt
import plotly.graph_objs as go

MQTTHOST = "mqtt.greyltc.com"
DASHHOST = "127.0.0.1"

topic = input("Enter topic to subscribe to [data]: ")
if topic == "":
    topic = "data"
print(f"Subscribing to mqtt://{MQTTHOST}/{topic}")


def format_graph(latest_data, fig):
    """Format the plot.

    Parameters
    ----------
    latest_data : list
        List containing latest message dictionary and data array.
    fig : plotly.graph_objs.Figure
        Plotly figure.

    Returns
    -------
    fig : plotly.graph_objs.Figure
        Updated plotly figure.
    """
    m, data = latest_data

    print(m, np.shape(data))

    if m["clear"] is not True:
        if m["type"] == "type1":
            xlabel = "time (s)"
            ylabel = m["ylabel"]
            trace1 = go.Scatter(
                x=data[:, 0], y=data[:, 1], mode="lines+markers", name="y1"
            )
            xmin = min(data[:, 0])
            xmax = max(data[:, 0])
            ymin = min(data[:, 1])
            ymax = max(data[:, 1])
            fig.add_trace(trace1)
            yaxis = {
                "title": f"{ylabel}",
                "ticks": "inside",
                "mirror": "ticks",
                "linecolor": "#444",
                "showline": True,
                "showgrid": False,
                "zeroline": True,
                "range": [ymin, ymax],
            }
            layout = {"yaxis": yaxis}

        elif m["type"] == "type2":
            xlabel = "voltage (V)"
            ylabel = "current (A)"
            trace1 = go.Scatter(
                x=data[:, 0], y=data[:, 1], mode="lines+markers", name="fwd"
            )
            trace2 = go.Scatter(
                x=data[:, 2], y=data[:, 3], mode="lines+markers", name="rev"
            )
            xmin = min(np.append(data[:, 0], data[:, 2]))
            xmax = max(np.append(data[:, 0], data[:, 2]))
            ymin = min(np.append(data[:, 1], data[:, 3]))
            ymax = max(np.append(data[:, 1], data[:, 3]))
            fig.add_trace(trace1)
            fig.add_trace(trace2)
            yaxis = {
                "title": f"{ylabel}",
                "ticks": "inside",
                "mirror": "ticks",
                "linecolor": "#444",
                "showline": True,
                "showgrid": False,
                "range": [ymin, ymax],
                "zeroline": True,
            }
            layout = {"yaxis": yaxis}

        elif m["type"] == "type3":
            xlabel = "time (s)"
            ylabel = "current (A) | power (W)"
            ylabel2 = "voltage (V)"
            trace1 = go.Scatter(
                x=data[:, 0], y=data[:, 1], mode="lines+markers", name="I", yaxis="y1",
            )
            trace2 = go.Scatter(
                x=data[:, 0], y=data[:, 2], mode="lines+markers", name="P", yaxis="y1",
            )
            trace3 = go.Scatter(
                x=data[:, 0], y=data[:, 3], mode="lines+markers", name="V", yaxis="y2",
            )
            xmin = min(data[:, 0])
            xmax = max(data[:, 0])
            ymin = min(np.append(data[:, 1], data[:, 2]))
            ymax = max(np.append(data[:, 1], data[:, 2]))
            ymin2 = min(data[:, 3])
            ymax2 = max(data[:, 3])
            fig.add_trace(trace1)
            fig.add_trace(trace2)
            fig.add_trace(trace3)
            yaxis = {
                "title": f"{ylabel}",
                "ticks": "inside",
                "mirror": True,
                "linecolor": "#444",
                "showline": True,
                "showgrid": False,
                "range": [ymin, ymax],
                "zeroline": True,
            }
            yaxis2 = {
                "title": f"{ylabel2}",
                "ticks": "inside",
                "linecolor": "#444",
                "showline": True,
                "side": "right",
                "showgrid": False,
                "range": [ymin2, ymax2],
                "zeroline": False,
                "overlaying": "y",
            }
            layout = {"yaxis": yaxis, "yaxis2": yaxis2}

        elif m["type"] == "type4":
            xlabel = "wavelength (nm)"
            ylabel = "eta (%)"
            ylabel2 = "j (A/m^2)"
            trace1 = go.Scatter(
                x=data[:, 0],
                y=data[:, 1],
                mode="lines+markers",
                name="eta",
                yaxis="y1",
            )
            trace2 = go.Scatter(
                x=data[:, 0], y=data[:, 2], mode="lines+markers", name="j", yaxis="y2",
            )
            xmin = min(data[:, 0])
            xmax = max(data[:, 0])
            ymin = min(data[:, 1])
            ymax = max(data[:, 1])
            ymin2 = min(data[:, 2])
            ymax2 = max(data[:, 2])
            fig.add_trace(trace1)
            fig.add_trace(trace2)
            yaxis = {
                "title": f"{ylabel}",
                "ticks": "inside",
                "mirror": True,
                "linecolor": "#444",
                "showline": True,
                "showgrid": False,
                "range": [ymin, ymax],
                "zeroline": True,
            }
            yaxis2 = {
                "title": f"{ylabel2}",
                "ticks": "inside",
                "linecolor": "#444",
                "showline": True,
                "side": "right",
                "showgrid": False,
                "range": [ymin2, ymax2],
                "zeroline": False,
                "overlaying": "y",
            }
            layout = {"yaxis": yaxis, "yaxis2": yaxis2}

        xaxis = {
            "title": f"{xlabel}",
            "ticks": "inside",
            "mirror": "ticks",
            "linecolor": "#444",
            "showline": True,
            "showgrid": False,
            "range": [xmin, xmax],
            "zeroline": True,
        }
        layout["xaxis"] = xaxis
        layout["plot_bgcolor"] = "rgba(0,0,0,0)"
        fig.update_layout(layout)

    return fig


# These are global variables to store and access incoming and plot data. In this
# example it's ok to global variables because only one client can write the variable
# values. However, in general, this will cause problems when multiple clients try to
# write the variable.
# See https://dash.plotly.com/sharing-data-between-callbacks
data = np.empty((0, 4))  # running data store
latest_data = [
    {"clear": True},
    data,
]  # latest msg and corresponding state of data store
layout = {
    "xaxis": {
        "title": "time (s)",
        "ticks": "inside",
        "mirror": True,
        "linecolor": "#444",
        "showline": True,
        "showgrid": False,
    },
    "yaxis": {
        "title": "voltage (V)",
        "ticks": "inside",
        "mirror": True,
        "linecolor": "#444",
        "showline": True,
        "showgrid": False,
    },
    "plot_bgcolor": "#fff",
}
fig = go.Figure(data=[], layout=layout)  # figure to display on initial load

app = dash.Dash(__name__)

app.layout = html.Div(
    [
        dcc.Graph(
            id="live-update-graph",
            animate=True,
            style={"width": "100vw", "height": "100vh"},
            figure=fig,
        ),
        dcc.Interval(
            id="interval-component",
            interval=1 * 1000,  # in milliseconds
            n_intervals=0,
        ),
    ]
)


@app.callback(
    dash.dependencies.Output("live-update-graph", "figure"),
    [dash.dependencies.Input("interval-component", "n_intervals")],
)
def update_graph_live(n):
    """Update graph."""
    # WARNING: it's usually a bad idea to use global variables with Dash
    global latest_data
    global layout

    fig = format_graph(latest_data, go.Figure(data=[], layout=layout))
    layout = fig.layout

    return fig


def on_message(mqttc, obj, msg):
    """Act on an MQTT msg.

    Append or clear data stored in global variables.
    """
    # WARNING: it's usually a bad idea to use global variables with Dash
    global data
    global latest_data

    m = json.loads(msg.payload)

    if m["clear"] is True:
        data = np.empty((0, 4))
    else:
        if m["type"] == "type1":
            data = np.append(data, np.array([[m["x1"], m["y1"], 0, 0]]), axis=0)
        elif m["type"] == "type2":
            data = np.array(m["data"])
        elif m["type"] == "type3":
            data = np.append(
                data, np.array([[m["x1"], m["y1"], m["y2"], m["y3"]]]), axis=0
            )
        elif m["type"] == "type4":
            data = np.append(data, np.array([[m["x1"], m["y1"], m["y2"], 0]]), axis=0)
        else:
            raise ValueError(f"Unsupported figure type: {m['type']}.")

    latest_data = [m, data]


# create client and connect to server
mqttc = mqtt.Client()
mqttc.on_message = on_message
mqttc.connect(MQTTHOST)
mqttc.subscribe(topic, qos=2)

# start new thread for mqtt client
mqttc.loop_start()

# start dash server
app.run_server(host=DASHHOST, debug=False)

# stop mqtt thread
mqttc.loop_stop()
