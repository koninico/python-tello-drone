import os
from flask import Flask

WEB_ADDRESS = '0.0.0.0'
WEB_PORT = 8000
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
TEMPLATES = os.path.join(PROJECT_ROOT, 'droneapp/templates')
STATIC_FOLDER = os.path.join(PROJECT_ROOT, 'droneapp/static')
DEBUG = False
LOG_FILE = 'ptell.log'

# Flaskアプリケーションの初期化
app = Flask(__name__, template_folder=TEMPLATES, static_folder=STATIC_FOLDER)

if DEBUG:
    app.debug = DEBUG