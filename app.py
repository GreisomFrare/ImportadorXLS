import os
import json
from flask import Flask, send_from_directory
from flask_cors import CORS
from models import init_db, close_db
from routes.oracle import oracle_bp
from routes.layouts import layouts_bp
from routes.importacao import importacao_bp

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = r'C:\Viasoft\Client\PlugIns\pluggy_config.json'

def get_port():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
        return cfg.get('server', {}).get('porta', 5000)
    return 5000

def create_app():
    app = Flask(__name__,
                static_folder=os.path.join(BASE_DIR, 'frontend'),
                static_url_path='')
    CORS(app)

    app.register_blueprint(oracle_bp, url_prefix='/api/oracle')
    app.register_blueprint(layouts_bp, url_prefix='/api/layouts')
    app.register_blueprint(importacao_bp, url_prefix='/api/import')

    app.teardown_appcontext(close_db)

    with app.app_context():
        init_db()

    @app.route('/')
    @app.route('/index.html')
    def index():
        return send_from_directory(os.path.join(BASE_DIR, 'frontend'), 'index.html')

    return app

if __name__ == '__main__':
    app = create_app()
    port = get_port()
    app.run(host='0.0.0.0', port=port, debug=True)
