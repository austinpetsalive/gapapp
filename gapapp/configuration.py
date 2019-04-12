import logging
import uuid

PORT = 8080
HOST = '127.0.0.1'
DEBUG = True

LOG_LEVEL = logging.INFO

SECRET_KEY = '620151038390181035037983056972'
STATIC_FILE_PATH = 'static'
DATA_PATH = './data/'
MAX_FIELD_LENGTH = 256
MAX_DATA_SIZE = 100

BLUE_SPECUTRUM = ["#8EB5CC", "#84AAC0", "#7A9FB5", "#7094AA", "#67899E", "#5D7E93", "#537388", "#4A687C", "#405D71", "#365266", "#2D485B"]
BLUE_ORANGE_SPECTRUM = ["#8EB5CC", "#96AABD", "#9F9FAE", "#A8959F", "#B18A90", "#BA8081", "#C27572", "#CB6A63", "#D46054", "#DD5545", "#E64B36"]

DEATH_COLOR = '#963022'
OWNER_REQUEST_EUTHANASIA_COLOR = '#842a1e'

def get_outcome_color(outcome_label):
    return {'adoption': BLUE_SPECUTRUM[0], 
            'return to owner': BLUE_SPECUTRUM[3], 
            'transfer out': BLUE_SPECUTRUM[6], 
            'lost/stolen': BLUE_SPECUTRUM[9],
            'death/euthanized': DEATH_COLOR, 
            'owner requested euthanasia': OWNER_REQUEST_EUTHANASIA_COLOR}[outcome_label.lower()]

CONTENT_FONT_FAMILY = 'Source Sans Pro, sans-serif'

OUTCOME_ORDER = ['death/euthanized', 'owner requested euthanasia', 'lost/stolen', 'transfer out', 'return to owner', 'adoption']
OUTCOME_RECOMMENDATIONS = [.05, 0, 0, .30, .20, .45]

DASHBOARD_LOCAL_SAVE_PATH = './static/dashboards/'
DASHBOARD_SERVER_SAVE_PATH = '/static/dashboards/'
