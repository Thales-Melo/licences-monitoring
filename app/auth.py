from flask import Blueprint, flash, session, redirect, url_for, request
from google_auth_oauthlib.flow import Flow, InstalledAppFlow
from config import Config
import json

main = Blueprint('main', __name__)

credentials_info = json.loads(Config.GOOGLE_CLIENT_SECRETS)

# Usa `from_client_config` em vez de `from_client_secrets_file`
flow = Flow.from_client_config(
    credentials_info,
    scopes=['https://www.googleapis.com/auth/drive'],
    redirect_uri=Config.REDIRECT_URI
)

@main.route('/authorize')
def authorize():
    # logging.debug('Authorizing...')
    authorization_url, state = flow.authorization_url(access_type='offline')
    session['state'] = state
    # logging.debug(f'Authorization URL: {authorization_url}')
    return redirect(authorization_url)

@main.route('/callback')
def callback():
    # Tente buscar o token
    flow.fetch_token(authorization_response=request.url)

    # Verifica se há um mismatch no state
    if session.get('state') != request.args.get('state'):
        # Adiciona um aviso ao sistema de mensagens
        flash('Erro de segurança: O estado não corresponde. Atualize a página e tente novamente.', 'warning')
        return redirect(url_for('index'))

    credentials = flow.credentials
    session['credentials'] = credentials_to_dict(credentials)
    return redirect(url_for('index'))

def save_credentials(credentials):
    session['credentials'] = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }

def credentials_to_dict(credentials):
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }

