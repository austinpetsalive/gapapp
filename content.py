import plotly.plotly as py
import plotly.graph_objs as go
from plotly.offline import plot
from plotly import tools

from uuid import uuid4

def get_dashboard_filenames():
    uuid = uuid4()
    local = './static/dashboards/{0}.html'.format(uuid)
    server = '/static/dashboards/{0}.html'.format(uuid)
    return local, server

def get_outcome_color(outcome_label):
    return {'death': '#882222', 'adoption': '#9EC5AB', 'return to owner': '#32746D', 'transfer': '#104F55'}[outcome_label.lower()]

def outcome_summary(df, expected_height):
    labels = list(df['Outcome'].value_counts().keys())
    values = list(df['Outcome'].value_counts())
    colors = [get_outcome_color(outcome) for outcome in labels]
    trace = go.Pie(labels=labels, values=values, name="Outcomes Summary", marker=dict(colors=colors, line=dict(color='#000000', width=2)))
    data = [trace]
    layout = go.Layout(
        title='Outcomes Summary',
        autosize=True,
        height=expected_height
    )
    fig = go.Figure(data=data, layout=layout)
    return plot(fig, auto_open=False, output_type='div', include_mathjax=False, include_plotlyjs=False)

def outcome_time_series(df, expected_height):
    traces = [go.Histogram(x=df[df['Outcome']==outcome]['Intake Date'], name=outcome.title(), marker=dict(color=get_outcome_color(outcome))) for outcome in list(df['Outcome'].value_counts().keys())]
    fig = go.Figure(data=traces, layout=go.Layout(barmode='stack', 
                                                  title="Outcomes Over Time", 
                                                  height=expected_height, 
                                                  autosize=True, 
                                                  margin={'autoexpand': True, 't': 0, 'pad': 0, 'r':0, 'l':0, 'b': 20}))
    return plot(fig, auto_open=False, output_type='div', include_mathjax=False, include_plotlyjs=False)

def recommendation_bubble(title, contents, bubble_class='positive'):
    assert bubble_class == 'positive' or bubble_class == 'negative' or bubble_class == 'neutral'
    bubble = """<div class='recommendationbubble {0}'><div class="bubblehead">{1}</div>{2}</div>""".format(bubble_class, title, contents)
    return bubble

def population_summary(df, expected_height):
    vals = df.groupby('Species')['Group'].value_counts().sort_index()
    row_labels, col_labels = [x.tolist() for x in vals.keys().levels]
    z = vals.values.reshape(2, 4)
    heatmap = go.Heatmap(z=z, x=col_labels, y=row_labels, colorscale='Viridis')
    hist = go.Histogram(x=df[df['Species'] == 'Dog']['Size'])
    fig = tools.make_subplots(rows=1, cols=2, subplot_titles=('Adult Dog Sizes', 'Population Totals'))
    fig.append_trace(hist, 1, 1)
    fig.append_trace(heatmap, 1, 2)
    fig['layout'].update(title='Critical Population Numbers', height=expected_height)
    return plot(fig, auto_open=False, output_type='div', include_mathjax=False, include_plotlyjs=False)


def overall_recommendation(df):
    outcome_counts = df['Outcome'].value_counts()
    total = len(df)
    if outcome_counts['Death']/total > 0.1:
        return recommendation_bubble('Needs Improvement', 'It looks like you might need some work on the number of animals that die. The next sections can help you narrow down the best way to address these animals!', 'negative')
    if outcome_counts['Death']/total <= 0.1 and outcome_counts['Death']/total > 0.5:
        return recommendation_bubble('Doing Good!', 'You\'re saving 90%! Great work! It looks like you\'re not to 95% yet though, so let\'s dig into your population and see where we might be able to squeeze out that last little bit.', 'neutral')
    if outcome_counts['Death']/total < 0.5:
        return recommendation_bubble('Great Job! You\'re saving more than 95%! It is often incredibly difficult to figure out how to save those last 5%, but see below to dig into that population and what you might be able to do for them.', 'positive')