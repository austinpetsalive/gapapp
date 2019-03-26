from flask import Flask, render_template, flash, request
from wtforms import Form, TextField, TextAreaField, validators, StringField, SubmitField
from sheets import get_sheet_data

from flask import send_from_directory, redirect

import pandas as pd
import time
import os

from plotly_demo import simple_plotly_figure

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
        return redirect(simple_plotly_figure(df))
        #return render_template()
    
    return render_template('main.html', form=form)
 
if __name__ == "__main__":
    app.run(host='192.168.2.4', port=8080, debug=True)