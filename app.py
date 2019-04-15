from flask import Flask, render_template, flash, request
from wtforms import Form, TextField, TextAreaField, validators, StringField, SubmitField

from flask import send_from_directory, redirect

import logging
import pandas as pd
import time
import os

import gapapp
import gapapp.configuration as cfg
import gapapp.utils as utils
from gapapp.content import ContentRenderer
from gapapp.sheets import get_sheet_data
from gapapp.data import save_data_to_file

logging.basicConfig(level=cfg.LOG_LEVEL, format='%(asctime)s %(message)s')

# App config.
DEBUG = True
app = Flask(__name__)
app.config.from_object(__name__)
app.config['SECRET_KEY'] = cfg.SECRET_KEY
static_file_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), cfg.STATIC_FILE_PATH)

class ReusableForm(Form):
    name = TextField('Google Sheets URL:', validators=[validators.required()])
    email = TextField('email')

@app.route("/", methods=['GET', 'POST'])
def hello():
    form = ReusableForm(request.form)

    logging.error(form.errors)
    if request.method == 'POST':
        URL = request.form['name']
        email = request.form['email']
        logging.info(email)
        logging.info(URL)
        data = get_sheet_data(URL)
        df = pd.DataFrame(data[1:], columns=data[0])
        save_data_to_file(df, email)
        logging.debug(df)

    if form.validate():
        # Save the comment here.
        flash(data)
        return redirect(make_dash(df))
    
    return render_template('main.html', form=form)
 
def make_dash(df):
    local, server = utils.get_dashboard_filenames()
    with open('./static/dashboard.html', 'r') as fp:
        dash = fp.read()
    if len(df) > cfg.MAX_DATA_SIZE:
        df = df.sample(n=cfg.MAX_DATA_SIZE)
    content = ContentRenderer(df)
    for key in content.CONTENT_LUT:
        t0 = time.time()
        if content.CONTENT_LUT[key][1]: # Check the required height parameter
            dash = dash.replace(key, content.CONTENT_LUT[key][0](content.CONTENT_LUT[key][1])) # If there is a required height parameter
        else:
            dash = dash.replace(key, content.CONTENT_LUT[key][0]()) # If there is no required height parameter
        delta_t = time.time() - t0
        logging.info(key + " (t={0})".format(delta_t))
    logging.info('Done')
    with open(local, 'w') as fp:
        fp.write(dash)
    return server

if __name__ == "__main__":
    app.run(host=cfg.HOST, port=cfg.PORT, debug=cfg.DEBUG)