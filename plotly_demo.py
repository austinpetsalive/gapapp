import plotly.plotly as py
import plotly.graph_objs as go
from plotly.offline import plot

from uuid import uuid4

def get_dashboard_filenames():
    uuid = uuid4()
    local = './static/dashboards/{0}'.format(uuid)
    server = '/static/dashboards/{0}.html'.format(uuid)
    return local, server

def get_demo():
    trace1 = go.Barpolar(
        r=[77.5, 72.5, 70.0, 45.0, 22.5, 42.5, 40.0, 62.5],
        text=['North', 'N-E', 'East', 'S-E', 'South', 'S-W', 'West', 'N-W'],
        name='11-14 m/s',
        marker=dict(
            color='rgb(106,81,163)'
        )
    )
    trace2 = go.Barpolar(
        r=[57.49999999999999, 50.0, 45.0, 35.0, 20.0, 22.5, 37.5, 55.00000000000001],
        text=['North', 'N-E', 'East', 'S-E', 'South', 'S-W', 'West', 'N-W'],
        name='8-11 m/s',
        marker=dict(
            color='rgb(158,154,200)'
        )
    )
    trace3 = go.Barpolar(
        r=[40.0, 30.0, 30.0, 35.0, 7.5, 7.5, 32.5, 40.0],
        text=['North', 'N-E', 'East', 'S-E', 'South', 'S-W', 'West', 'N-W'],
        name='5-8 m/s',
        marker=dict(
            color='rgb(203,201,226)'
        )
    )
    trace4 = go.Barpolar(
        r=[20.0, 7.5, 15.0, 22.5, 2.5, 2.5, 12.5, 22.5],
        text=['North', 'N-E', 'East', 'S-E', 'South', 'S-W', 'West', 'N-W'],
        name='< 5 m/s',
        marker=dict(
            color='rgb(242,240,247)'
        )
    )
    data = [trace1, trace2, trace3, trace4]
    layout = go.Layout(
        title='Wind Speed Distribution in Laurel, NE',
        font=dict(
            size=16
        ),
        legend=dict(
            font=dict(
                size=16
            )
        ),
        radialaxis=dict(
            ticksuffix='%'
        ),
        orientation=270
    )
    fig = go.Figure(data=data, layout=layout)
    local, server = get_dashboard_filenames()
    plot(fig, filename=local, auto_open=False)
    return server

def simple_plotly_figure(df):
    labels = list(df['Outcome'].value_counts().keys())
    values = list(df['Outcome'].value_counts())

    trace = go.Pie(labels=labels, values=values)
    
    local, server = get_dashboard_filenames()
    plot([trace], filename=local, auto_open=False)
    return server