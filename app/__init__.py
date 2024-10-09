# __init__.py
import os
import time
import logging
import schedule
from flask import Flask
from google_auth_oauthlib.flow import Flow
from datetime import datetime
from config import Config  # Importa a classe Config
# from .db import db  # Importa a variável db do arquivo db.py



def create_app():
    app = Flask(__name__, template_folder='templates')
    
    # Carregar as configurações a partir da classe Config
    app.config.from_object(Config)

    # Configurar o diretório do script como o diretório principal
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    # Configurar a chave secreta
    update_secret_key(app)

    # Configurar OAuth (Google Drive) utilizando as configurações do Config
    app.config['GOOGLE_CLIENT_SECRETS'] = app.config['GOOGLE_CLIENT_SECRETS']
    app.config['REDIRECT_URI'] = app.config['REDIRECT_URI']

    # Desativar a verificação de transporte inseguro (Somente para desenvolvimento local)
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = app.config['OAUTHLIB_INSECURE_TRANSPORT']

    # Configurar blueprints (importa as rotas)
    from .routes import main
    app.register_blueprint(main)

    return app

def update_secret_key(app):
    app.secret_key = os.urandom(24)
    print("Secret key updated.")
    print(f"DATA -> {datetime.now().strftime('%d/%m/%Y')} \nHORÁRIO -> {datetime.now().strftime('%H:%M:%S')}")

def schedule_secret_key_update(app):
    # Agenda a execução da função a cada 1 hora
    schedule.every(1).hour.do(lambda: update_secret_key(app))

    while True:
        schedule.run_pending()
        time.sleep(1)
