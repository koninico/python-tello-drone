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

# セッション管理のためのSECRET_KEY
# 本番環境では環境変数から読み込むことを推奨
import os
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'drone-control-secure-key-2024-change-in-production')

if DEBUG:
    app.debug = DEBUG