#!/usr/bin/env python
"""Plot data obtained from MQTT broker using Dash."""

import collections
import json

import dash
import dash_core_components as dcc
import dash_html_components as html
import numpy as np
import paho.mqtt.client as mqtt
import plotly
import plotly.graph_objs as go

MQTTHOST = "mqtt.greyltc.com"
DASHHOST = "127.0.0.1"

topic = input("Enter topic to subscribe to [data]: ")
if topic == "":
    topic = "data"
print(f"Subscribing to mqtt://{MQTTHOST}/{topic}")


def format_graph(msg, data, fig):
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
    if msg["clear"] is not True:
        if msg["type"] == "type1":
            xlabel = "time (s)"
            ylabel = msg["ylabel"]
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

        elif msg["type"] == "type2":
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

        elif msg["type"] == "type3":
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

        elif msg["type"] == "type4":
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


def format_figure_1(data, fig, title="-"):
    """Format figure type 1.

    Parameters
    ----------
    data : array
        Array of data.
    fig : plotly.graph_objs.Figure
        Plotly figure.
    title : str
        Title of plot.

    Returns
    -------
    fig : plotly.graph_objs.Figure
        Updated plotly figure.
    """
    # clear old data from figure
    fig["data"] = []
    if len(data) == 0:
        # if request to clear has been issued, return cleared figure
        return fig
    else:
        # add data to fig
        trace1 = go.Scatter(x=data[:, 0], y=data[:, 1], mode="lines+markers", name="v")
        fig.add_trace(trace1)

        # update ranges
        xrange = [min(data[:, 0]), max(data[:, 0])]
        yrange = [min(data[:, 1]), max(data[:, 1])]
        fig.update_layout(xaxis={"range": xrange}, yaxis={"range": yrange})

        # update title
        annotations = list(fig.layout.annotations)
        annotations[0]["text"] = title
        fig.layout.annotations = tuple(annotations)

        return fig


def format_figure_2(data, fig, title="-"):
    """Format figure type 2.

    Parameters
    ----------
    data : array
        Array of data.
    fig : plotly.graph_objs.Figure
        Plotly figure.
    title : str
        Title of plot.

    Returns
    -------
    fig : plotly.graph_objs.Figure
        Updated plotly figure.
    """
    # clear old data from figure
    fig["data"] = []
    if len(data) == 0:
        # if request to clear has been issued, return cleared figure
        return fig
    else:
        # add data to fig
        trace1 = go.Scatter(
            x=data[:, 0], y=data[:, 1], mode="lines+markers", name="fwd"
        )
        trace2 = go.Scatter(
            x=data[:, 2], y=data[:, 3], mode="lines+markers", name="rev"
        )
        fig.add_trace(trace1)
        fig.add_trace(trace2)

        # update ranges
        xrange = [
            min(np.append(data[:, 0], data[:, 2])),
            max(np.append(data[:, 0], data[:, 2])),
        ]
        yrange = [
            min(np.append(data[:, 1], data[:, 3])),
            max(np.append(data[:, 1], data[:, 3])),
        ]
        fig.update_layout(xaxis={"range": xrange}, yaxis={"range": yrange})

        # update title
        annotations = list(fig.layout.annotations)
        annotations[0]["text"] = title
        fig.layout.annotations = tuple(annotations)

        return fig


def format_figure_3(data, fig, title="-"):
    """Format figure type 3.

    Parameters
    ----------
    data : array
        Array of data.
    fig : plotly.graph_objs.Figure
        Plotly figure.
    title : str
        Title of plot.

    Returns
    -------
    fig : plotly.graph_objs.Figure
        Updated plotly figure.
    """
    # clear old data from figure
    fig["data"] = []
    if len(data) == 0:
        # if request to clear has been issued, return cleared figure
        return fig
    else:
        # add data to fig
        trace1 = go.Scatter(x=data[:, 0], y=data[:, 1], mode="lines+markers", name="i")
        trace2 = go.Scatter(x=data[:, 0], y=data[:, 2], mode="lines+markers", name="p")
        trace3 = go.Scatter(x=data[:, 0], y=data[:, 3], mode="lines+markers", name="v")
        fig.add_trace(trace1)
        fig.add_trace(trace2)
        fig.add_trace(trace3, secondary_y=True)

        # update ranges
        xrange = [min(data[:, 0]), max(data[:, 0])]
        yrange = [
            min(np.append(data[:, 1], data[:, 2])),
            max(np.append(data[:, 1], data[:, 2])),
        ]
        yrange2 = [min(data[:, 3]), max(data[:, 3])]
        fig.update_layout(
            xaxis={"range": xrange}, yaxis={"range": yrange}, yaxis2={"range": yrange2}
        )

        # update title
        annotations = list(fig.layout.annotations)
        annotations[0]["text"] = title
        fig.layout.annotations = tuple(annotations)

        return fig


def format_figure_4(data, fig, title="-"):
    """Format figure type 4.

    Parameters
    ----------
    data : array
        Array of data.
    fig : plotly.graph_objs.Figure
        Plotly figure.
    title : str
        Title of plot.

    Returns
    -------
    fig : plotly.graph_objs.Figure
        Updated plotly figure.
    """
    # clear old data from figure
    fig["data"] = []
    if len(data) == 0:
        # if request to clear has been issued, return cleared figure
        return fig
    else:
        # add data to fig
        trace1 = go.Scatter(x=data[:, 0], y=data[:, 1], mode="lines+markers", name="j")
        fig.add_trace(trace1)

        # update ranges
        xrange = [min(data[:, 0]), max(data[:, 0])]
        yrange = [min(data[:, 1]), max(data[:, 1])]
        fig.update_layout(xaxis={"range": xrange}, yaxis={"range": yrange})

        # update title
        annotations = list(fig.layout.annotations)
        annotations[0]["text"] = title
        fig.layout.annotations = tuple(annotations)

        return fig


def format_figure_5(data, fig, title="-"):
    """Format figure type 5.

    Parameters
    ----------
    data : array
        Array of data.
    fig : plotly.graph_objs.Figure
        Plotly figure.
    title : str
        Title of plot.

    Returns
    -------
    fig : plotly.graph_objs.Figure
        Updated plotly figure.
    """
    # clear old data from figure
    fig["data"] = []
    if len(data) == 0:
        # if request to clear has been issued, return cleared figure
        return fig
    else:
        # add data to fig
        trace1 = go.Scatter(
            x=data[:, 0], y=data[:, 1], mode="lines+markers", name="eta"
        )
        trace2 = go.Scatter(x=data[:, 0], y=data[:, 2], mode="lines+markers", name="j")
        fig.add_trace(trace1)
        fig.add_trace(trace2, secondary_y=True)

        # update ranges
        xrange = [min(data[:, 0]), max(data[:, 0])]
        yrange = [min(data[:, 1]), min(data[:, 1])]
        yrange2 = [min(data[:, 2]), min(data[:, 2])]
        fig.update_layout(
            xaxis={"range": xrange}, yaxis={"range": yrange}, yaxis2={"range": yrange2}
        )

        # update title
        annotations = list(fig.layout.annotations)
        annotations[0]["text"] = title
        fig.layout.annotations = tuple(annotations)

        return fig


# create thread-safe containers for storing latest data and plot info
graph1_latest = collections.deque(maxlen=1)
graph2_latest = collections.deque(maxlen=1)
graph3_latest = collections.deque(maxlen=1)
graph4_latest = collections.deque(maxlen=1)
graph5_latest = collections.deque(maxlen=1)

# initialise plot info/data queues
graph1_latest.append({"msg": {"clear": True, "id": "-"}, "data": np.empty((0, 2))})
graph2_latest.append({"msg": {"clear": True, "id": "-"}, "data": np.empty((0, 4))})
graph3_latest.append({"msg": {"clear": True, "id": "-"}, "data": np.empty((0, 4))})
graph4_latest.append({"msg": {"clear": True, "id": "-"}, "data": np.empty((0, 2))})
graph5_latest.append({"msg": {"clear": True, "id": "-"}, "data": np.empty((0, 3))})

# initial figure properties
fig1 = plotly.subplots.make_subplots(rows=1, cols=1, subplot_titles=["-"])
fig1.add_trace(go.Scatter(x=[], y=[], mode="lines+markers", name="v"))
fig1.update_xaxes(
    title="time (s)",
    ticks="inside",
    mirror="ticks",
    linecolor="#444",
    showline=True,
    zeroline=False,
    showgrid=False,
)
fig1.update_yaxes(
    title="voltage (V)",
    ticks="inside",
    mirror="ticks",
    linecolor="#444",
    showline=True,
    zeroline=False,
    showgrid=False,
)
fig1.update_layout(margin=dict(l=20, r=0, t=30, b=0), plot_bgcolor="rgba(0,0,0,0)")

fig2 = plotly.subplots.make_subplots(rows=1, cols=1, subplot_titles=["-"])
fig2.add_trace(go.Scatter(x=[], y=[], mode="lines+markers", name="fwd"))
fig2.add_trace(go.Scatter(x=[], y=[], mode="lines+markers", name="rev"))
fig2.update_xaxes(
    title="voltage (V)",
    ticks="inside",
    mirror="ticks",
    linecolor="#444",
    showline=True,
    zeroline=False,
    showgrid=False,
)
fig2.update_yaxes(
    title="current (A)",
    ticks="inside",
    mirror="ticks",
    linecolor="#444",
    showline=True,
    zeroline=False,
    showgrid=False,
)
fig2.update_layout(margin=dict(l=20, r=0, t=30, b=0), plot_bgcolor="rgba(0,0,0,0)")

fig3 = plotly.subplots.make_subplots(
    rows=1, cols=1, specs=[[{"secondary_y": True}]], subplot_titles=["-"]
)
fig3.add_trace(go.Scatter(x=[], y=[], mode="lines+markers", name="j"))
fig3.add_trace(go.Scatter(x=[], y=[], mode="lines+markers", name="p"))
fig3.add_trace(go.Scatter(x=[], y=[], mode="lines+markers", name="v"), secondary_y=True)
fig3.update_xaxes(
    title="time (s)",
    ticks="inside",
    mirror="ticks",
    linecolor="#444",
    showline=True,
    zeroline=False,
    showgrid=False,
)
fig3.update_yaxes(
    title="current (A) | power (W)",
    ticks="inside",
    mirror=True,
    linecolor="#444",
    showline=True,
    zeroline=False,
    showgrid=False,
)
fig3.update_yaxes(
    title="voltage (V)",
    ticks="inside",
    mirror=True,
    linecolor="#444",
    showline=True,
    zeroline=False,
    showgrid=False,
    overlaying="y",
    secondary_y=True,
)
fig3.update_layout(margin=dict(l=20, r=0, t=30, b=0), plot_bgcolor="rgba(0,0,0,0)")

fig4 = plotly.subplots.make_subplots(rows=1, cols=1, subplot_titles=["-"])
fig4.add_trace(go.Scatter(x=[], y=[], mode="lines+markers", name="j"))
fig4.update_xaxes(
    title="time (s)",
    ticks="inside",
    mirror="ticks",
    linecolor="#444",
    showline=True,
    zeroline=False,
    showgrid=False,
)
fig4.update_yaxes(
    title="current (A)",
    ticks="inside",
    mirror="ticks",
    linecolor="#444",
    showline=True,
    zeroline=False,
    showgrid=False,
)
fig4.update_layout(margin=dict(l=20, r=0, t=30, b=0), plot_bgcolor="rgba(0,0,0,0)")

fig5 = plotly.subplots.make_subplots(
    rows=1, cols=1, specs=[[{"secondary_y": True}]], subplot_titles=["-"]
)
fig5.add_trace(go.Scatter(x=[], y=[], mode="lines+markers", name="eta"))
fig5.add_trace(go.Scatter(x=[], y=[], mode="lines+markers", name="j"), secondary_y=True)
fig5.update_xaxes(
    title="wavelength (nm)",
    ticks="inside",
    mirror="ticks",
    linecolor="#444",
    showline=True,
    zeroline=False,
    showgrid=False,
)
fig5.update_yaxes(
    title="eqe (%)",
    ticks="inside",
    mirror=True,
    linecolor="#444",
    showline=True,
    zeroline=False,
    showgrid=False,
)
fig5.update_yaxes(
    title="integrated j (A/m^2)",
    ticks="inside",
    mirror=True,
    linecolor="#444",
    showline=True,
    zeroline=False,
    showgrid=False,
    overlaying="y",
    secondary_y=True,
)
fig5.update_layout(margin=dict(l=20, r=0, t=30, b=0), plot_bgcolor="rgba(0,0,0,0)")


app = dash.Dash(__name__)

# style={"width": "100vw", "height": "100vh"},

app.layout = html.Div(
    [
        html.Div(
            [
                html.Div(
                    [dcc.Graph(id="g1", animate=True, figure=fig1,)],
                    className="four columns",
                ),
                html.Div(
                    [dcc.Graph(id="g2", animate=True, figure=fig2,)],
                    className="four columns",
                ),
                html.Div(
                    [dcc.Graph(id="g3", animate=True, figure=fig3,)],
                    className="four columns",
                ),
            ],
            className="row",
        ),
        html.Div(
            [
                html.Div(
                    [dcc.Graph(id="g4", animate=True, figure=fig4,)],
                    className="four columns",
                ),
                html.Div(
                    [dcc.Graph(id="g5", animate=True, figure=fig5,)],
                    className="four columns",
                ),
            ],
            className="row",
        ),
        dcc.Interval(
            id="interval-component",
            interval=1 * 1000,  # in milliseconds
            n_intervals=0,
        ),
    ],
)


@app.callback(
    [
        dash.dependencies.Output("g1", "figure"),
        dash.dependencies.Output("g2", "figure"),
        dash.dependencies.Output("g3", "figure"),
        dash.dependencies.Output("g4", "figure"),
        dash.dependencies.Output("g5", "figure"),
    ],
    [dash.dependencies.Input("interval-component", "n_intervals")],
    [
        dash.dependencies.State("g1", "figure"),
        dash.dependencies.State("g2", "figure"),
        dash.dependencies.State("g3", "figure"),
        dash.dependencies.State("g4", "figure"),
        dash.dependencies.State("g5", "figure"),
    ],
)
def update_graph_live(n, g1, g2, g3, g4, g5):
    """Update graph."""
    g1_latest = graph1_latest[0]
    g2_latest = graph2_latest[0]
    g3_latest = graph3_latest[0]
    g4_latest = graph4_latest[0]
    g5_latest = graph5_latest[0]

    # update figures
    fig1 = format_figure_1(g1_latest["data"], g1, g1_latest["msg"]["id"])
    fig2 = format_figure_2(g2_latest["data"], g2, g2_latest["msg"]["id"])
    fig3 = format_figure_3(g3_latest["data"], g3, g3_latest["msg"]["id"])
    fig4 = format_figure_4(g4_latest["data"], g4, g4_latest["msg"]["id"])
    fig5 = format_figure_5(g5_latest["data"], g5, g5_latest["msg"]["id"])

    return fig1, fig2, fig3, fig4, fig5


# MQTT on_message callback functions for each graph
def on_message_1(mqttc, obj, msg):
    """Act on an MQTT msg.

    Append or clear data stored in a queue.
    """
    m = json.loads(msg.payload)
    data = graph1_latest[0]["data"]

    if m["clear"] is True:
        data = np.empty((0, 2))
    else:
        data = np.append(data, np.array([[m["x1"], m["y1"]]]), axis=0)

    graph1_latest.append({"msg": m, "data": data})


def on_message_2(mqttc, obj, msg):
    """Act on an MQTT msg.

    Append or clear data stored in a queue.
    """
    m = json.loads(msg.payload)
    data = graph2_latest[0]["data"]

    if m["clear"] is True:
        data = np.empty((0, 4))
    else:
        data = np.array(m["data"])

    graph2_latest.append({"msg": m, "data": data})


def on_message_3(mqttc, obj, msg):
    """Act on an MQTT msg.

    Append or clear data stored in a queue.
    """
    m = json.loads(msg.payload)
    data = graph3_latest[0]["data"]

    if m["clear"] is True:
        data = np.empty((0, 4))
    else:
        data = np.append(data, np.array([[m["x1"], m["y1"], m["y2"], m["y3"]]]), axis=0)

    graph3_latest.append({"msg": m, "data": data})


def on_message_4(mqttc, obj, msg):
    """Act on an MQTT msg.

    Append or clear data stored in a queue.
    """
    m = json.loads(msg.payload)
    data = graph4_latest[0]["data"]

    if m["clear"] is True:
        data = np.empty((0, 2))
    else:
        data = np.append(data, np.array([[m["x1"], m["y1"]]]), axis=0)

    graph4_latest.append({"msg": m, "data": data})


def on_message_5(mqttc, obj, msg):
    """Act on an MQTT msg.

    Append or clear data stored in a queue.
    """
    m = json.loads(msg.payload)
    data = graph5_latest[0]["data"]

    if m["clear"] is True:
        data = np.empty((0, 3))
    else:
        data = np.append(data, np.array([[m["x1"], m["y1"], m["y2"]]]), axis=0)

    graph5_latest.append({"msg": m, "data": data})


subtopics = []
subtopics.append(f"{topic}/exp1")
subtopics.append(f"{topic}/exp2")
subtopics.append(f"{topic}/exp3")
subtopics.append(f"{topic}/exp4")
subtopics.append(f"{topic}/exp5")

on_messages = [on_message_1, on_message_2, on_message_3, on_message_4, on_message_5]

# start a new mqtt subscriber client for each subtopic, each in its own thread
mqtt_clients = []
for subtopic, on_msg in zip(subtopics, on_messages):
    mqttc = mqtt.Client()
    mqtt_clients.append(mqttc)
    mqttc.on_message = on_msg
    mqttc.connect(MQTTHOST)
    mqttc.subscribe(subtopic, qos=2)
    mqttc.loop_start()

# start dash server
app.run_server(host=DASHHOST, debug=False)

# stop mqtt client threads
for mqttc in mqtt_clients:
    mqttc.loop_stop()
    mqttc.disconnect()
