import gapapp.configuration as cfg
from colour import Color
import numpy as np
from uuid import uuid4
import os

def get_dashboard_filenames():
    uuid = uuid4()
    local = os.path.join(cfg.DASHBOARD_LOCAL_SAVE_PATH, '{0}.html'.format(uuid))
    server = os.path.join(cfg.DASHBOARD_SERVER_SAVE_PATH, '{0}.html'.format(uuid))
    return local, server

desaturate_color = lambda c, percent: Color(hsl=np.array(Color(c).hsl) * np.array([1., percent, 1.])).hex

def resort_outcomes(labels, values, empty_value=0):
    order = cfg.OUTCOME_ORDER
    lower_labels = [l.lower() for l in labels]
    new_labels = []
    new_values = []
    for o in order:
        if o in lower_labels:
            idx = lower_labels.index(o)
            new_labels.append(labels[idx])
            new_values.append(values[idx])
        else:
            new_labels.append(o.title())
            new_values.append(empty_value)
    return new_labels, new_values


def recommendation_bubble(title, contents, bubble_class='positive'):
    assert bubble_class == 'positive' or bubble_class == 'negative' or bubble_class == 'neutral'
    bubble = """<div class='recommendationbubble {0}'><div class="bubblehead">{1}</div>{2}</div>""".format(bubble_class, title, contents)
    return bubble


def html_table(lol):
    html = ""
    html += '<table class="table striped">'
    for sublist in lol:
        html += '  <tr><td>'
        html += '    </td><td>'.join([str(x) for x in sublist])
        html += '  </td></tr>'
    html += '</table>'
    return html
