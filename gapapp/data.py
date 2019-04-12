import time
import os

import gapapp.configuration as cfg

def save_data_to_file(df, email):
    timestr = time.strftime("%Y%m%d-%H%M%S")
    if email.strip() == '':
        email = 'none'
    else:
        keepcharacters = (' ','.','_')
        email = "".join(c for c in email.strip() if c.isalnum() or c in keepcharacters).rstrip()
        email = email[0:cfg.MAX_FIELD_LENGTH].strip()
    df.to_pickle(os.path.join(cfg.DATA_PATH, '{1}-{0}.pkl'.format(timestr, email)))
