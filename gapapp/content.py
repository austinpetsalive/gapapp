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


class ContentRenderer():
    def __init__(self, df):
        self.CONTENT_LUT = {
            '{{plots.outcome_summary}}': [self.outcome_summary, 550],
            '{{recommendations.overall}}': [self.overall_recommendation, None],
            '{{plots.outcome_time_series}}': [self.outcome_time_series, 200],
            '{{plots.population_summary}}': [self.population_summary, 600],
            '{{tables.outcome_summary}}': [self.get_outcomes_table, None],
            '{{tables.population}}': [self.get_population_table, None],
            '{{plots.population_outcomes}}': [self.population_outcomes_graph, 600],
            '{{plots.population_outcomes_conditions}}': [self.population_outcomes_condition_graph, 600],
            '{{tables.population_outcomes_conditions}}': [self.population_outcomes_table, None],
            '{{tables.population_outcomes_conditions_table}}': [self.population_outcomes_conditions_table_all, None],
            '{{recommendations.housing}}': [self.housing_recommendation, None],
            '{{tables.subpopulation_conditions}}': [self.get_subpop_condition_tables, None]
        }
        self.src_df = df

    def get_outcomes_data(self):
        df = self.src_df
        labels = list(df['Outcome'].value_counts().keys())
        values = list(df['Outcome'].value_counts())
        labels, values = utils.resort_outcomes(labels, values)
        return labels, values

    def outcome_summary(self, expected_height):
        # Get data
        labels, values = self.get_outcomes_data()
        labels_merged = []
        values_merged = []
        death_value_merged = 0
        for idx, (l, v) in enumerate(zip(labels, values)):
            if idx in cfg.OUTCOME_DEATH_INDICIES:
                death_value_merged += v
            else:
                labels_merged.append(l)
                values_merged.append(v)
        labels_merged.append('Death')
        values_merged.append(death_value_merged)
        labels = labels_merged
        values = values_merged
        
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

    def outcome_time_series(self, expected_height):
        df = self.src_df
        # Get data
        labels, _ = self.get_outcomes_data()

        outcomes = labels
        # Make time series histogram
        traces = []
        for outcome in outcomes:
            dat = df[df['Outcome']==outcome]['Intake Date']
            if len(dat) > 0:
                traces.append(go.Histogram(x=dat, name=outcome.title(), marker=dict(color=cfg.get_outcome_color(outcome))))
            else:
                traces.append(go.Histogram(x=[], name=outcome.title(), marker=dict(color=cfg.get_outcome_color(outcome))))
        # Sort outcomes in plot
        outcomes, traces = utils.resort_outcomes(outcomes, traces)

        # Define plot
        fig = go.Figure(data=traces, layout=go.Layout(barmode='stack', 
                                                    title="Outcomes Over Time", 
                                                    height=expected_height, 
                                                    autosize=True, 
                                                    margin={'autoexpand': True, 't': 35, 'pad': 0, 'r':10, 'l':20, 'b': 20},
                                                    font=dict(family=cfg.CONTENT_FONT_FAMILY)))
        return plot(fig, auto_open=False, output_type='div', include_mathjax=False, include_plotlyjs=False)

    def get_population_data(self):
        df = self.src_df
        vals = df.groupby('Species')['Group'].value_counts().sort_index()
        row_labels, col_labels = [x.tolist() for x in vals.keys().levels]
        z = np.array(df.groupby(['Species','Group']).size().to_frame('count').reset_index().merge(
            pd.DataFrame(list(set([i for i in product(*[df.Group, df.Species])])), columns=['Group', 'Species']),
            on=['Species', 'Group'],
            how='right').fillna(value=0)['count']).reshape(2, 4)
        return row_labels, col_labels, z

    def population_summary(self, expected_height):
        df = self.src_df
        # Get data
        row_labels, col_labels, z = self.get_population_data()

        # Get colors
        custom_colors = list(zip(np.linspace(0, 1, len(cfg.BLUE_SPECUTRUM)),cfg.BLUE_SPECUTRUM))

        # Define figures
        heatmap = go.Heatmap(z=z, x=col_labels, y=row_labels, colorscale=custom_colors, reversescale=True, name="Population")#'Viridis')
        hist = go.Histogram(x=df[df['Species'] == 'Dog']['Size'], marker=dict(color=cfg.BLUE_SPECUTRUM[0]), name="Population")

        # Create subplots and layout
        fig = tools.make_subplots(rows=1, cols=2, subplot_titles=('Adult Dog Sizes', 'Population Totals'), print_grid=False)
        fig.append_trace(hist, 1, 1)
        fig.append_trace(heatmap, 1, 2)
        fig['layout'].update(title='Critical Population Numbers', height=expected_height)
        fig['layout'].update(margin={'b': 150, 'r': 150})
        fig['layout'].update(font=dict(family=cfg.CONTENT_FONT_FAMILY))
        return plot(fig, auto_open=False, output_type='div', include_mathjax=False, include_plotlyjs=False)

    def overall_recommendation(self):
        df = self.src_df
        # Get data
        _, values = self.get_outcomes_data()
        
        good_threshold = 0.1
        great_threshold = 0.05

        # Determine outcomes
        outcome_deaths = sum([values[i] for i in cfg.OUTCOME_DEATH_INDICIES])
        total = len(df)
        if total == 0:
            return utils.recommendation_bubble('No Data Found', 'It looks like there wasn\'t any data found. Please report this as an error if it is not expected.', 'neutral')
        outcome_death_rate = outcome_deaths/total
        
        if outcome_death_rate > good_threshold:
            return utils.recommendation_bubble('Needs Improvement', 'Your save rate is {0:0.1f}%. In general, a good save rate is considered to be 90% or greater. The next sections can help you narrow down the best way to address these animals!'.format((1-outcome_death_rate)*100.0), 'negative')
        if outcome_death_rate <= good_threshold and outcome_death_rate > great_threshold:
            return utils.recommendation_bubble('Doing Good!', 'You\'re saving {0:0.1f}%! Great work! It looks like you\'re not to {1}% yet though, so let\'s dig into your population and see where we might be able to squeeze out that last little bit.'.format((1-outcome_death_rate)*100.0, int((1-great_threshold)*100)), 'neutral')
        if outcome_death_rate < great_threshold:
            return utils.recommendation_bubble('Great Job!', 'You\'re saving {1:0.1f}%! It is often incredibly difficult to figure out how to save those last {0}%, but see below to dig into that population and what you might be able to do for them.'.format(int(great_threshold*100), (1-outcome_death_rate)*100.0), 'positive')

    def housing_recommendation(self):
        df = self.src_df
        df = df[df['Species'] == 'Dog']
        df = df[[x or y for x, y in zip(df['Group'] == 'Adult (6 months to 7 years)',  df['Group'] == 'Senior (7 years and older)')]]
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
        return utils.recommendation_bubble('Housing Recommendation', 'Based on the {0} days of data on adult dogs, {1} single housed, and {2} co-housed animals, we recommend you have {3} kennels at a minimum.'.format(days, single_housing, co_housing, recommendation), 'neutral')

    def get_outcomes_table(self):
        labels, values = self.get_outcomes_data()
        labels_merged = []
        values_merged = []
        death_value_merged = 0
        for idx, (l, v) in enumerate(zip(labels, values)):
            if idx in cfg.OUTCOME_DEATH_INDICIES:
                death_value_merged += v
            else:
                labels_merged.append(l)
                values_merged.append(v)
        labels_merged.append('Death')
        values_merged.append(death_value_merged)
        labels = labels_merged
        values = values_merged
        
        rec = cfg.OUTCOME_RECOMMENDATIONS
        display_percents = ['{0}%'.format(int(x)) for x in np.round(np.array(rec)*100)]
        display_estimates = np.round(np.array(rec)*np.sum(values)).astype(int)
        deltas = [y-x for x, y in zip(values, display_estimates)]
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

    def get_population_table(self):
        df = self.src_df
        vals = df.groupby('Species')['Group'].value_counts().sort_index()
        row_labels, col_labels = [x.tolist() for x in vals.keys().levels]
        
        z = np.array(df.groupby(['Species','Group']).size().to_frame('count').reset_index().merge(
            pd.DataFrame(list(set([i for i in product(*[df.Group, df.Species])])), columns=['Group', 'Species']),
            on=['Species', 'Group'],
            how='right').fillna(value=0)['count']).reshape(2, 4).astype(int)
        rows = []
        rows.append([''] + col_labels)
        total = 0
        for zz in z:
            total += sum(zz)
        for label, zz in zip(row_labels, z):
            counts = list(zz)
            if total > 0:
                percents = ['{0:0.1f}%'.format(float(x)/total*100) for x in counts]
            else:
                percents = ['na' for _ in counts]
            display_numbers = ['{0} ({1})'.format(c, p) for c, p in zip(counts, percents)]
            rows.append([label] + display_numbers)
        return utils.html_table(rows)

    def get_pop_breakdown(self):
        df = self.src_df
        # z = df.groupby(['Species', 'Group', 'Outcome']).size().to_frame('count').reset_index().merge(
        # pd.DataFrame(list(set([i for i in product(*[df.Outcome, df.Group, df.Species])])), columns=['Outcome', 'Group', 'Species']),
        # on=['Species', 'Group', 'Outcome'],
        # how='right').fillna(value=0)
        # z['GroupLabel'] = z['Species'] + ', ' + z['Group']
        species_values = ['Dog', 'Cat']
        group_values = ['Neonatal (less than 6 weeks)', 'Puppies/Kittens (6 weeks to 6 months)', 'Adult (6 months to 12 years)', 'Senior (12 years and older)']
        outcome_values = ['Died in Care', 'Death/Euthanized', 'Owner Requested Euthanasia', 'Lost/Stolen', 'Transfer Out', 'Return to Owner', 'Adoption']
        combinations = product(species_values, group_values, outcome_values)
        outcomes, count, grouplabels = [], [], []
        for s, g, o in combinations:
            ss, gg, oo = df['Species'] == s, df['Group'] == g, df['Outcome'] == o
            outcomes.append(o)
            grouplabels.append(' '.join([s, g]))
            count.append(float([a and b and c for a, b, c in zip(ss, gg, oo)].count(True)))
        z = pd.DataFrame(np.transpose([outcomes, count, grouplabels]), columns=['Outcome', 'count', 'GroupLabel'])
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

    def population_outcomes_graph(self, expected_height):
        labels, stacks, stacks_norm = self.get_pop_breakdown()
        
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

    def population_outcomes_table(self):
        labels, stacks, _ = self.get_pop_breakdown()
        labels = [l.replace('/', '/ ') for l in labels]
        rows = []
        rows.append([''] + labels)
        total = 0
        for key in stacks:
            for x in stacks[key]:
                total += int(x)
        for key in stacks:
            counts = [int(x) for x in stacks[key]]
            if total > 0:
                percents = ['{0:0.1f}%'.format(float(x)/total*100) for x in counts]
            else:
                percents = ['na' for _ in counts]
            display_numbers = ['{0} ({1})'.format(c, p) for c, p in zip(counts, percents)]
            rows.append([key.split('(')[0]] + display_numbers)
        return '<div style="overflow: auto; height: 450px">' + utils.html_table(rows).replace('<table', '<table style="font-size: 12px;"') + '</div>'

    def get_cod_breakdown(self, df):
        z = df.groupby(['Reason for Death', 'Outcome']).size().to_frame('count').reset_index().merge(
        pd.DataFrame(list(set([i for i in product(*[df['Outcome'], df['Reason for Death']])])), columns=['Outcome', 'Reason for Death']),
        on=['Reason for Death', 'Outcome'],
        how='right').fillna(value=0)
        # z['GroupLabel'] = z['Species'] + ', ' + z['Group']
        grps = z.groupby(['Reason for Death', 'Outcome'])['count']
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

    def create_outcomes_condition_traces(self, df, default_visibilty=False):
        traces = []
        traces_norm = []

        if len(df) == 0:
            labels = [o.title() for o in cfg.OUTCOME_ORDER]
            for idx, label in enumerate(labels):
                traces.append(go.Bar(x=[], y=[], name=label, marker=dict(color=cfg.get_outcome_color(label)), visible=default_visibilty))
                traces_norm.append(go.Bar(x=[], y=[], name=label, marker=dict(color=cfg.get_outcome_color(label)), visible=False))
        else:
            labels, stacks, stacks_norm = self.get_cod_breakdown(df)
            for idx, label in enumerate(labels):
                traces.append(go.Bar(x=[l.split('(')[0] for l in list(stacks.keys())],
                                    y=np.transpose(list(stacks.values()))[idx],
                                    name=label,
                                    marker=dict(color=cfg.get_outcome_color(label)), visible=default_visibilty))
                traces_norm.append(go.Bar(x=[l.split('(')[0] for l in list(stacks_norm.keys())],
                                    y=np.transpose(list(stacks_norm.values()))[idx],
                                    name=label,
                                    marker=dict(color=cfg.get_outcome_color(label)), visible=False))
        
        all_traces = traces+traces_norm

        return all_traces

    @staticmethod
    def get_data_visibility(group_number, norm, n_traces, n_traces_per_fascet):
            vis = [False for _ in range(n_traces)]
            if norm:
                start_idx = group_number*n_traces_per_fascet*2 + n_traces_per_fascet
            else:
                start_idx = group_number*n_traces_per_fascet*2
            vis[start_idx:start_idx+n_traces_per_fascet] = [True for _ in range(n_traces_per_fascet)]
            return vis

    def population_outcomes_condition_graph(self, expected_height):
        df = self.src_df
        all_traces = self.create_outcomes_condition_traces(df, default_visibilty=True)
        n_traces_per_fascet = int(len(all_traces)/2.)
        subpops = [
            [x and y for x, y in zip(df['Group'] == 'Neonatal (less than 6 weeks)', df['Species'] == 'Cat')],
            [x and y for x, y in zip(df['Group'] == 'Puppies/Kittens (6 weeks to 6 months)', df['Species'] == 'Cat')],
            [x and y for x, y in zip(df['Group'] == 'Adult (6 months to 12 years)', df['Species'] == 'Cat')],
            [x and y for x, y in zip(df['Group'] == 'Senior (12 years and older)', df['Species'] == 'Cat')],

            [x and y for x, y in zip(df['Group'] == 'Neonatal (less than 6 weeks)', df['Species'] == 'Dog')],
            [x and y for x, y in zip(df['Group'] == 'Puppies/Kittens (6 weeks to 6 months)', df['Species'] == 'Dog')],
            [x and y for x, y in zip(df['Group'] == 'Adult (6 months to 12 years)', df['Species'] == 'Dog')],
            [x and y for x, y in zip(df['Group'] == 'Senior (12 years and older)', df['Species'] == 'Dog')]
        ]
        for population in subpops:
            subpop_traces = self.create_outcomes_condition_traces(df[population])
            all_traces = all_traces + subpop_traces
        n_traces = len(all_traces)
        get_vis = lambda grp: self.get_data_visibility(grp, False, n_traces, n_traces_per_fascet)
        get_vis_norm = lambda grp: self.get_data_visibility(grp, True, n_traces, n_traces_per_fascet)
        layout = go.Layout(barmode='stack', title="Raw Outcomes by Condition", margin={'b': 150}, height=expected_height)
        fig = go.Figure(data=all_traces, layout=layout)
        fig['layout'].update(font=dict(family=cfg.CONTENT_FONT_FAMILY))
        fig['layout'].update(updatemenus=list([
                                            dict(
                                                buttons=list([   
                                                    dict(label='All', method='update', args=[{'visible': get_vis(0)}]),
                                                    dict(label='% All', method='update', args=[{'visible': get_vis_norm(0)}]),
                                                    dict(label='Neonatal Cats', method='update', args=[{'visible': get_vis(1)}]),
                                                    dict(label='Kitten', method='update', args=[{'visible': get_vis(2)}]),
                                                    dict(label='Adult Cats', method='update', args=[{'visible': get_vis(3)}]),
                                                    dict(label='Senior Cats', method='update', args=[{'visible': get_vis(4)}]),
                                                    dict(label='Neonatal Dogs', method='update', args=[{'visible': get_vis(5)}]),
                                                    dict(label='Puppies', method='update', args=[{'visible': get_vis(6)}]),
                                                    dict(label='Adult Dogs', method='update', args=[{'visible': get_vis(7)}]),
                                                    dict(label='Seniors Dogs', method='update', args=[{'visible': get_vis(8)}]),
                                                    dict(label='% Neonatal', method='update', args=[{'visible': get_vis_norm(1)}]),
                                                    dict(label='% Kitten', method='update', args=[{'visible': get_vis_norm(2)}]),
                                                    dict(label='% Adult Cats', method='update', args=[{'visible': get_vis_norm(3)}]),
                                                    dict(label='% Senior Cats', method='update', args=[{'visible': get_vis_norm(4)}]),
                                                    dict(label='% Neonatal Dogs', method='update', args=[{'visible': get_vis_norm(5)}]),
                                                    dict(label='% Puppies', method='update', args=[{'visible': get_vis_norm(6)}]),
                                                    dict(label='% Adult Dogs', method='update', args=[{'visible': get_vis_norm(7)}]),
                                                    dict(label='% Seniors Dogs', method='update', args=[{'visible': get_vis_norm(8)}]),
                                                ]),
                                                direction = 'down',
                                                pad = {'r': 10, 't': 10},
                                                showactive = True,
                                                x = 0.1,
                                                xanchor = 'left',
                                                y = 1.1,
                                                yanchor = 'top' 
                                            )
                                        ]))
        return plot(fig, auto_open=False, output_type='div', include_mathjax=False, include_plotlyjs=False)

    def population_outcomes_conditions_table_all(self):
        return self.population_outcomes_conditions_table(self.src_df)

    def population_outcomes_conditions_table(self, df, auto_height=False):
        if len(df) == 0:
            labels = [o.title() for o in cfg.OUTCOME_ORDER]
            stacks = {}
        else:
            labels, stacks, _ = self.get_cod_breakdown(df)
        labels = [l.replace('/', '/ ') for l in labels]
        rows = []
        rows.append([''] + labels)
        total = 0
        for key in stacks:
            for x in stacks[key]:
                total += int(x)
        for key in stacks:
            counts = [int(x) for x in stacks[key]]
            if total > 0:
                percents = ['{0:0.1f}%'.format(float(x)/total*100) for x in counts]
            else:
                percents = ['na' for _ in counts]
            display_numbers = ['{0} ({1})'.format(c, p) for c, p in zip(counts, percents)]
            rows.append([key.split('(')[0]] + display_numbers)
        if auto_height:
            prefix = '<div style="overflow: auto;">'
        else:
            prefix = '<div style="overflow: auto; height: 450px">'
        return prefix + utils.html_table(rows).replace('<table', '<table style="font-size: 12px;"') + '</div>'

    def get_subpop_condition_tables(self):
        df = self.src_df
        subpops = [
            [x and y for x, y in zip(df['Group'] == 'Neonatal (less than 6 weeks)', df['Species'] == 'Cat')],
            [x and y for x, y in zip(df['Group'] == 'Puppies/Kittens (6 weeks to 6 months)', df['Species'] == 'Cat')],
            [x and y for x, y in zip(df['Group'] == 'Adult (6 months to 12 years)', df['Species'] == 'Cat')],
            [x and y for x, y in zip(df['Group'] == 'Senior (12 years and older)', df['Species'] == 'Cat')],

            [x and y for x, y in zip(df['Group'] == 'Neonatal (less than 6 weeks)', df['Species'] == 'Dog')],
            [x and y for x, y in zip(df['Group'] == 'Puppies/Kittens (6 weeks to 6 months)', df['Species'] == 'Dog')],
            [x and y for x, y in zip(df['Group'] == 'Adult (6 months to 12 years)', df['Species'] == 'Dog')],
            [x and y for x, y in zip(df['Group'] == 'Senior (12 years and older)', df['Species'] == 'Dog')]
        ]
        tbls = [self.population_outcomes_conditions_table(df[pop], auto_height=True) for pop in subpops]
        header_tempalte = '<h2 class="subheader">{0}</h2>'
        headers = ['Neonatal Cats', 'Kittens', 'Adult Cats', 'Senior Cats', 'Neonatal Dogs', 'Puppies', 'Adult Dogs', 'Senior Dogs']
        tables = ''
        for header, tbl in zip(headers, tbls):
            tables += header_tempalte.format(header) + tbl + '<hr>'
        return tables

    