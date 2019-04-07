import plotly.plotly as py
import plotly.graph_objs as go
from plotly.offline import plot
from plotly import tools
from itertools import product
import numpy as np
import pandas as pd

from uuid import uuid4

def get_dashboard_filenames():
    uuid = uuid4()
    local = './static/dashboards/{0}.html'.format(uuid)
    server = '/static/dashboards/{0}.html'.format(uuid)
    return local, server

BLUE_SPECUTRUM = ["#8EB5CC", "#84AAC0", "#7A9FB5", "#7094AA", "#67899E", "#5D7E93", "#537388", "#4A687C", "#405D71", "#365266", "#2D485B"]
BLUE_ORANGE_SPECTRUM = ["#8EB5CC", "#96AABD", "#9F9FAE", "#A8959F", "#B18A90", "#BA8081", "#C27572", "#CB6A63", "#D46054", "#DD5545", "#E64B36"]

def get_outcome_color(outcome_label):
    return {'adoption': BLUE_SPECUTRUM[0], 
            'return to owner': BLUE_SPECUTRUM[3], 
            'transfer out': BLUE_SPECUTRUM[6], 
            'lost/stolen': BLUE_SPECUTRUM[9],
            'death/euthanized': '#963022', 
            'owner requested euthanasia': '#842a1e'}[outcome_label.lower()]
def get_font():
    return dict(family='Source Sans Pro, sans-serif')

def outcome_summary(df, expected_height):
    labels = list(df['Outcome'].value_counts().keys())
    values = list(df['Outcome'].value_counts())
    colors = [get_outcome_color(outcome) for outcome in labels]
    trace = go.Pie(labels=labels, values=values, name="Outcomes Summary", marker=dict(colors=colors, line=dict(color='#000000', width=2)))
    data = [trace]
    layout = go.Layout(
        title='Outcomes Summary',
        autosize=True,
        height=expected_height,
        font=get_font()
    )
    fig = go.Figure(data=data, layout=layout)
    return plot(fig, auto_open=False, output_type='div', include_mathjax=False, include_plotlyjs=False)

def outcome_time_series(df, expected_height):
    traces = [go.Histogram(x=df[df['Outcome']==outcome]['Intake Date'], name=outcome.title(), marker=dict(color=get_outcome_color(outcome))) for outcome in list(df['Outcome'].value_counts().keys())]
    fig = go.Figure(data=traces, layout=go.Layout(barmode='stack', 
                                                  title="Outcomes Over Time", 
                                                  height=expected_height, 
                                                  autosize=True, 
                                                  margin={'autoexpand': True, 't': 35, 'pad': 0, 'r':10, 'l':20, 'b': 20},
                                                  font=get_font()))
    return plot(fig, auto_open=False, output_type='div', include_mathjax=False, include_plotlyjs=False)

def recommendation_bubble(title, contents, bubble_class='positive'):
    assert bubble_class == 'positive' or bubble_class == 'negative' or bubble_class == 'neutral'
    bubble = """<div class='recommendationbubble {0}'><div class="bubblehead">{1}</div>{2}</div>""".format(bubble_class, title, contents)
    return bubble

def population_summary(df, expected_height):
    vals = df.groupby('Species')['Group'].value_counts().sort_index()
    row_labels, col_labels = [x.tolist() for x in vals.keys().levels]
    z = np.array(df.groupby(['Species','Group']).size().to_frame('count').reset_index().merge(
        pd.DataFrame(list(set([i for i in product(*[df.Group, df.Species])])), columns=['Group', 'Species']),
        on=['Species', 'Group'],
        how='right').fillna(value=0)['count']).reshape(2, 4)
    custom_colors = list(zip(np.linspace(0, 1, len(BLUE_ORANGE_SPECTRUM)), BLUE_ORANGE_SPECTRUM))
    heatmap = go.Heatmap(z=z, x=col_labels, y=row_labels, colorscale=custom_colors)#'Viridis')
    hist = go.Histogram(x=df[df['Species'] == 'Dog']['Size'], marker=dict(color=BLUE_SPECUTRUM[0]))
    fig = tools.make_subplots(rows=1, cols=2, subplot_titles=('Adult Dog Sizes', 'Population Totals'))
    fig.append_trace(hist, 1, 1)
    fig.append_trace(heatmap, 1, 2)
    fig['layout'].update(title='Critical Population Numbers', height=expected_height)
    return plot(fig, auto_open=False, output_type='div', include_mathjax=False, include_plotlyjs=False)


def overall_recommendation(df):
    outcome_counts = df['Outcome'].value_counts()
    total = len(df)
    if outcome_counts['Death/Euthanized']/total > 0.1:
        return recommendation_bubble('Needs Improvement', 'It looks like you might need some work on the number of animals that die. The next sections can help you narrow down the best way to address these animals!', 'negative')
    if outcome_counts['Death/Euthanized']/total <= 0.1 and outcome_counts['Death']/total > 0.5:
        return recommendation_bubble('Doing Good!', 'You\'re saving 90%! Great work! It looks like you\'re not to 95% yet though, so let\'s dig into your population and see where we might be able to squeeze out that last little bit.', 'neutral')
    if outcome_counts['Death/Euthanized']/total < 0.5:
        return recommendation_bubble('Great Job! You\'re saving more than 95%! It is often incredibly difficult to figure out how to save those last 5%, but see below to dig into that population and what you might be able to do for them.', 'positive')