from itertools import product
from uuid import uuid4

import numpy as np
import pandas as pd

import plotly.graph_objs as go
import plotly.plotly as py
from colour import Color
from plotly import tools
from plotly.offline import plot

import gapapp.utils as utils
import gapapp.configuration as cfg


def run_query_function(query_func, df):
    name = query_func.func_name
    if name in QUERY_LUT:
        return QUERY_LUT[name]
    else:
        result = query_func(df)
        QUERY_LUT[name] = result
        return result


def get_outcomes_data(df):
    labels = list(df['Outcome'].value_counts().keys())
    values = list(df['Outcome'].value_counts())
    labels, values = utils.resort_outcomes(labels, values)
    return labels, values

def outcome_summary(df, expected_height):
    # Get data
    labels, values = run_query_function(get_outcomes_data, df)

    # Get colors
    colors = [cfg.get_outcome_color(outcome) for outcome in labels]
    faded_colors = [utils.desaturate_color(c, 0.5) for c in colors]

    # Define plots
    trace = go.Pie(labels=labels, values=values, 
                   name="Your Values", marker=dict(colors=colors, line=dict(color='#000000', width=2)), 
                   sort=False, hole=0.7)
    trace_target = go.Pie(labels=labels, values=np.array(cfg.OUTCOME_RECOMMENDATIONS) * np.sum(values), 
                          name="Target", marker=dict(colors=faded_colors, line=dict(color='#000000', width=2)), 
                          sort=False, hole=0.5, textinfo='none', hoverinfo='label+percent+name')

    # Define layout
    data = [trace_target, trace]
    layout = go.Layout(
        title='Outcomes Summary',
        autosize=True,
        height=expected_height,
        font=dict(family=cfg.CONTENT_FONT_FAMILY),
        legend=dict(x=-0.5, y=1.1)
    )

    # Create figure
    fig = go.Figure(data=data, layout=layout)
    return plot(fig, auto_open=False, output_type='div', include_mathjax=False, include_plotlyjs=False)

def outcome_time_series(df, expected_height):
    # Get data
    labels, values = run_query_function(get_outcomes_data, df)

    outcomes = labels
    # Make time series histogram
    traces = []
    for outcome in outcomes:
        dat = df[df['Outcome']==outcome]['Intake Date']
        if len(dat) > 0: #TODO: Fix issue with zero days not rendering properly
            traces.append(go.Histogram(x=dat, name=outcome.title(), marker=dict(color=cfg.get_outcome_color(outcome))))
    # Sort outcomes in plot
    outcomes, traces = utils.resort_outcomes(outcomes, traces)

    # TODO: Fix bug that makes this necessary
    outcomes_no_zeros = []
    traces_no_zeros = []
    for o, t in zip(outcomes, traces):
        if t != 0:
            outcomes_no_zeros.append(o)
            traces_no_zeros.append(t)
    outcomes, traces = outcomes_no_zeros, traces_no_zeros

    # Define plot
    fig = go.Figure(data=traces, layout=go.Layout(barmode='stack', 
                                                  title="Outcomes Over Time", 
                                                  height=expected_height, 
                                                  autosize=True, 
                                                  margin={'autoexpand': True, 't': 35, 'pad': 0, 'r':10, 'l':20, 'b': 20},
                                                  font=dict(family=cfg.CONTENT_FONT_FAMILY)))
    return plot(fig, auto_open=False, output_type='div', include_mathjax=False, include_plotlyjs=False)


def get_population_data(df):
    vals = df.groupby('Species')['Group'].value_counts().sort_index()
    row_labels, col_labels = [x.tolist() for x in vals.keys().levels]
    z = np.array(df.groupby(['Species','Group']).size().to_frame('count').reset_index().merge(
        pd.DataFrame(list(set([i for i in product(*[df.Group, df.Species])])), columns=['Group', 'Species']),
        on=['Species', 'Group'],
        how='right').fillna(value=0)['count']).reshape(2, 4)
    return row_labels, col_labels, z

def population_summary(df, expected_height):
    # Get data
    row_labels, col_labels, z = run_query_function(get_population_data, df)

    # Get colors
    custom_colors = list(zip(np.linspace(0, 1, len(cfg.BLUE_ORANGE_SPECTRUM)),cfg.BLUE_ORANGE_SPECTRUM))

    # Define figures
    heatmap = go.Heatmap(z=z, x=col_labels, y=row_labels, colorscale=custom_colors)#'Viridis')
    hist = go.Histogram(x=df[df['Species'] == 'Dog']['Size'], marker=dict(color=cfg.BLUE_SPECUTRUM[0]))

    # Create subplots and layout
    fig = tools.make_subplots(rows=1, cols=2, subplot_titles=('Adult Dog Sizes', 'Population Totals'))
    fig.append_trace(hist, 1, 1)
    fig.append_trace(heatmap, 1, 2)
    fig['layout'].update(title='Critical Population Numbers', height=expected_height)
    fig['layout'].update(margin={'b': 150, 'r': 150})
    fig['layout'].update(font=dict(family=cfg.CONTENT_FONT_FAMILY))
    return plot(fig, auto_open=False, output_type='div', include_mathjax=False, include_plotlyjs=False)


def overall_recommendation(df):
    # Get data
    labels, values = run_query_function(get_outcomes_data, df)
    
    good_threshold = 0.1
    great_threshold = 0.05
    # Determine outcomes
    outcome_counts = values
    total = len(df)
    #TODO: Make strings populate from threshold variables
    if outcome_counts['Death/Euthanized']/total > good_threshold:
        return utils.recommendation_bubble('Needs Improvement', 'It looks like you might need some work on the number of animals that die. The next sections can help you narrow down the best way to address these animals!', 'negative')
    if outcome_counts['Death/Euthanized']/total <= good_threshold and outcome_counts['Death/Euthanized']/total > great_threshold:
        return utils.recommendation_bubble('Doing Good!', 'You\'re saving 90%! Great work! It looks like you\'re not to 95% yet though, so let\'s dig into your population and see where we might be able to squeeze out that last little bit.', 'neutral')
    if outcome_counts['Death/Euthanized']/total < great_threshold:
        return utils.recommendation_bubble('Great Job! You\'re saving more than 95%! It is often incredibly difficult to figure out how to save those last 5%, but see below to dig into that population and what you might be able to do for them.', 'positive')

def housing_recommendation(df):
    single_ratio = 1.0/25.0
    co_ratio = 1.0/40.0
    intake = pd.to_datetime(df['Intake Date'])
    min_date = min(intake)
    max_date = max(intake)
    days = float((max_date - min_date).days)
    year_proportion = 365.25/days
    single_housing = (df['Housing Need'] == 'Single Unit Housing').count()
    single_housing_extrap = single_housing * year_proportion
    co_housing = (df['Housing Need'] == 'Co-Housing').count()
    co_housing_extrap = co_housing * year_proportion
    
    recommendation = int(np.ceil(single_housing_extrap*single_ratio + co_housing_extrap*co_ratio))
    return utils.recommendation_bubble('Housing Recommendation', 'Based on the {0} days of data, {1} single housed, and {2} co-housed animals, we recommend you have {3} kennels at a minimum.'.format(days, single_housing, co_housing, recommendation), 'neutral')

def get_outcomes_table(df):
    labels = list(df['Outcome'].value_counts().keys())
    values = list(df['Outcome'].value_counts())
    labels, values = utils.resort_outcomes(labels, values)
    rec = cfg.OUTCOME_RECOMMENDATIONS
    display_percents = ['{0}%'.format(int(x)) for x in np.round(np.array(rec)*100)]
    display_estimates = np.round(np.array(rec)*np.sum(values)).astype(int)
    deltas = [x-y for x, y in zip(values, display_estimates)]
    display_deltas = []
    for d in deltas:
        if d > 0:
            display_deltas.append('+{0}'.format(d))
        else:
            display_deltas.append('{0}'.format(d))
    #colors = [get_outcome_color(outcome) for outcome in labels]
    header = ['', 'Your Outcomes', 'Target %', 'Target #', 'Target Change']
    rows = [header] + list(zip(labels, values, display_percents, display_estimates, display_deltas))
    return utils.html_table(rows)

def get_population_table(df):
    vals = df.groupby('Species')['Group'].value_counts().sort_index()
    row_labels, col_labels = [x.tolist() for x in vals.keys().levels]
    z = np.array(df.groupby(['Species','Group']).size().to_frame('count').reset_index().merge(
        pd.DataFrame(list(set([i for i in product(*[df.Group, df.Species])])), columns=['Group', 'Species']),
        on=['Species', 'Group'],
        how='right').fillna(value=0)['count']).reshape(2, 4).astype(int)
    rows = []
    rows.append([''] + col_labels)
    for label, zz in zip(row_labels, z):
        rows.append([label] + list(zz))
    return utils.html_table(rows)

def get_pop_breakdown(df):
    z = df.groupby(['Species', 'Group', 'Outcome']).size().to_frame('count').reset_index().merge(
       pd.DataFrame(list(set([i for i in product(*[df.Outcome, df.Group, df.Species])])), columns=['Outcome', 'Group', 'Species']),
       on=['Species', 'Group', 'Outcome'],
       how='right').fillna(value=0)
    z['GroupLabel'] = z['Species'] + ', ' + z['Group']
    grps = z.groupby(['GroupLabel', 'Outcome'])['count']
    stacks = {}
    stacks_norm = {}
    labels = []
    for grp, val in grps:
        if grp[1] not in labels:
            labels.append(grp[1])
        if grp[0] in stacks:
            stacks[grp[0]].append(float(val))
        else:
            stacks[grp[0]] = [float(val)]
    for key in stacks:
        total = np.sum(stacks[key])
        if total == 0:
            stacks_norm[key] = [0 for _ in stacks[key]]
        else:
            stacks_norm[key] = [np.round(float(x)/float(total)*100, decimals=1) for x in stacks[key]]
    for key in stacks:
        _, stacks[key] = utils.resort_outcomes(labels, stacks[key])
    for key in stacks_norm:
        _, stacks_norm[key] = utils.resort_outcomes(labels, stacks_norm[key])
    labels, _ = utils.resort_outcomes(labels, list(range(len(labels))))
    return labels, stacks, stacks_norm

def population_outcomes_graph(df, expected_height):
    labels, stacks, stacks_norm = get_pop_breakdown(df)
    traces = []
    traces_norm = []
    for idx, label in enumerate(labels):
        traces.append(go.Bar(x=list(stacks.keys()),
                            y=np.transpose(list(stacks.values()))[idx],
                            name=label,
                            marker=dict(color=cfg.get_outcome_color(label))))
        traces_norm.append(go.Bar(x=list(stacks_norm.keys()),
                            y=np.transpose(list(stacks_norm.values()))[idx],
                            name=label,
                            marker=dict(color=cfg.get_outcome_color(label)), visible=False))
    def getDataVisibile(norm=False):
        if norm:
            return [False for _ in traces] + [True for _ in traces_norm]
        else:
            return [True for _ in traces] + [False for _ in traces_norm]
    layout = go.Layout(barmode='stack', title="Raw Outcomes by Group", margin={'b': 150}, height=expected_height)
    fig = go.Figure(data=traces+traces_norm, layout=layout)
    fig['layout'].update(font=dict(family=cfg.CONTENT_FONT_FAMILY))
    fig['layout'].update(updatemenus=list([
                                        dict(
                                            buttons=list([   
                                                dict(label = 'Raw Numbers',
                                                    method = 'update',
                                                    args = [{'visible': getDataVisibile(False)},
                                                            {'title': 'Raw Outcomes by Group'}]
                                                ),
                                                dict(label = 'Percentages',
                                                    method = 'update', 
                                                    args = [{'visible': getDataVisibile(True)},
                                                            {'title': 'Percent Outcomes by Group'}]
                                                ),                    
                                            ]),
                                            direction = 'left',
                                            pad = {'r': 10, 't': 10},
                                            showactive = True,
                                            type = 'buttons',
                                            x = 0.1,
                                            xanchor = 'left',
                                            y = 1.1,
                                            yanchor = 'top' 
                                        )
                                    ]))
    return plot(fig, auto_open=False, output_type='div', include_mathjax=False, include_plotlyjs=False)

def population_outcomes_table(df):
    labels, stacks, _ = get_pop_breakdown(df)
    labels = [l.replace('/', '/ ') for l in labels]
    rows = []
    rows.append([''] + labels)
    for key in stacks:
        rows.append([key] + [int(x) for x in stacks[key]])
    return '<div style="overflow: auto; height: 450px">' + utils.html_table(rows).replace('<table', '<table style="font-size: 12px;"') + '</div>'

def get_cod_breakdown(df):
    z = df.groupby(['Cause of Death (if applicable)', 'Outcome']).size().to_frame('count').reset_index().merge(
       pd.DataFrame(list(set([i for i in product(*[df['Outcome'], df['Cause of Death (if applicable)']])])), columns=['Outcome', 'Cause of Death (if applicable)']),
       on=['Cause of Death (if applicable)', 'Outcome'],
       how='right').fillna(value=0)
    # z['GroupLabel'] = z['Species'] + ', ' + z['Group']
    grps = z.groupby(['Cause of Death (if applicable)', 'Outcome'])['count']
    stacks = {}
    stacks_norm = {}
    labels = []
    for grp, val in grps:
        if grp[1] not in labels:
            labels.append(grp[1])
        if grp[0] in stacks:
            stacks[grp[0]].append(float(val))
        else:
            stacks[grp[0]] = [float(val)]
    for key in stacks:
        total = np.sum(stacks[key])
        if total == 0:
            stacks_norm[key] = [0 for _ in stacks[key]]
        else:
            stacks_norm[key] = [np.round(float(x)/float(total)*100, decimals=1) for x in stacks[key]]
    for key in stacks:
        _, stacks[key] = utils.resort_outcomes(labels, stacks[key])
    for key in stacks_norm:
        _, stacks_norm[key] = utils.resort_outcomes(labels, stacks_norm[key])
    labels, _ = utils.resort_outcomes(labels, list(range(len(labels))))
    return labels, stacks, stacks_norm

def population_outcomes_cause_graph(df, expected_height):
    labels, stacks, stacks_norm = get_cod_breakdown(df)
    traces = []
    traces_norm = []
    for idx, label in enumerate(labels):
        traces.append(go.Bar(x=list(stacks.keys()),
                            y=np.transpose(list(stacks.values()))[idx],
                            name=label,
                            marker=dict(color=cfg.get_outcome_color(label))))
        traces_norm.append(go.Bar(x=list(stacks_norm.keys()),
                            y=np.transpose(list(stacks_norm.values()))[idx],
                            name=label,
                            marker=dict(color=cfg.get_outcome_color(label)), visible=False))
    def getDataVisibile(norm=False):
        if norm:
            return [False for _ in traces] + [True for _ in traces_norm]
        else:
            return [True for _ in traces] + [False for _ in traces_norm]
    layout = go.Layout(barmode='stack', title="Raw Outcomes by Cause", margin={'b': 150}, height=expected_height)
    fig = go.Figure(data=traces+traces_norm, layout=layout)
    fig['layout'].update(font=dict(family=cfg.CONTENT_FONT_FAMILY))
    fig['layout'].update(updatemenus=list([
                                        dict(
                                            buttons=list([   
                                                dict(label = 'Raw Numbers',
                                                    method = 'update',
                                                    args = [{'visible': getDataVisibile(False)},
                                                            {'title': 'Raw Outcomes by Cause'}]
                                                ),
                                                dict(label = 'Percentages',
                                                    method = 'update', 
                                                    args = [{'visible': getDataVisibile(True)},
                                                            {'title': 'Percent Outcomes by Cause'}]
                                                ),                    
                                            ]),
                                            direction = 'left',
                                            pad = {'r': 10, 't': 10},
                                            showactive = True,
                                            type = 'buttons',
                                            x = 0.1,
                                            xanchor = 'left',
                                            y = 1.1,
                                            yanchor = 'top' 
                                        )
                                    ]))
    return plot(fig, auto_open=False, output_type='div', include_mathjax=False, include_plotlyjs=False)

def population_outcomes_causes_table(df):
    labels, stacks, _ = get_cod_breakdown(df)
    labels = [l.replace('/', '/ ') for l in labels]
    rows = []
    rows.append([''] + labels)
    for key in stacks:
        rows.append([key] + [int(x) for x in stacks[key]])
    return '<div style="overflow: auto; height: 450px">' + utils.html_table(rows).replace('<table', '<table style="font-size: 12px;"') + '</div>'

CONTENT_LUT = {
    '{{plots.outcome_summary}}': [outcome_summary, 600],
    '{{recommendations.overall}}': [overall_recommendation, None],
    '{{plots.outcome_time_series}}': [outcome_time_series, 200],
    '{{plots.population_summary}}': [population_summary, 600],
    '{{tables.outcome_summary}}': [get_outcomes_table, None],
    '{{tables.population}}': [get_population_table, None],
    '{{plots.population_outcomes}}': [population_outcomes_graph, 600],
    '{{plots.population_outcomes_causes}}': [population_outcomes_cause_graph, 600],
    '{{tables.population_outcomes_causes}}': [population_outcomes_table, None],
    '{{tables.population_outcomes_causes_table}}': [population_outcomes_causes_table, None],
    '{{recommendations.housing}}': [housing_recommendation, None],
}


QUERY_LUT = {

}