from flask import Flask, render_template, flash, request
from wtforms import Form, TextField, TextAreaField, validators, StringField, SubmitField
from sheets import get_sheet_data

from flask import send_from_directory, redirect

import pandas as pd
import time
import os

import content

# App config.
DEBUG = True
app = Flask(__name__)
app.config.from_object(__name__)
app.config['SECRET_KEY'] = '620151038390181035037983056972'
static_file_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'static')

class ReusableForm(Form):
    name = TextField('Google Sheets URL:', validators=[validators.required()])
    email = TextField('email')

@app.route("/", methods=['GET', 'POST'])
def hello():
    form = ReusableForm(request.form)

    print(form.errors)
    if request.method == 'POST':
        URL = request.form['name']
        email = request.form['email']
        print(email)
        print(URL)
        data = get_sheet_data(URL)
        df = pd.DataFrame(data[1:], columns=data[0])
        timestr = time.strftime("%Y%m%d-%H%M%S")
        if email == '':
            email = 'none'
        else:
            keepcharacters = (' ','.','_')
            email = "".join(c for c in email if c.isalnum() or c in keepcharacters).rstrip()
            email = email[0:256]
        df.to_pickle('./data/{1}-{0}.pkl'.format(timestr, email))
        print(df)

    if form.validate():
        # Save the comment here.
        flash(data)
        return redirect(make_dash(df))
    
    return render_template('main.html', form=form)
 
def make_dash(df):
    local, server =content.get_dashboard_filenames()
    with open('./static/dashboard.html', 'r') as fp:
        dash = fp.read()
    dash = dash.replace('{{plots.outcome_summary}}', content.outcome_summary(df, 600))
    dash = dash.replace('{{recommendations.overall}}', content.overall_recommendation(df))
    dash = dash.replace('{{plots.outcome_time_series}}', content.outcome_time_series(df, 200))
    dash = dash.replace('{{plots.population_summary}}', content.population_summary(df, 600))
    dash = dash.replace('{{tables.outcome_summary}}', content.get_outcomes_table(df))
    dash = dash.replace('{{tables.population}}', content.get_population_table(df))
    dash = dash.replace('{{plots.population_outcomes}}', content.population_outcomes_graph(df, 600))
    dash = dash.replace('{{plots.population_outcomes_causes}}', content.population_outcomes_cause_graph(df, 600))
    dash = dash.replace('{{tables.population_outcomes_causes}}', content.population_outcomes_table(df))
    dash = dash.replace('{{tables.population_outcomes_causes_table}}', content.population_outcomes_causes_table(df))
    dash = dash.replace('{{recommendations.housing}}', content.housing_recommendation(df))
    with open(local, 'w') as fp:
        fp.write(dash)
    return server

if __name__ == "__main__":
    app.run(host='192.168.2.4', port=8080, debug=True)