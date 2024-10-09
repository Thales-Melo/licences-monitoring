from flask import Blueprint, session, redirect, url_for, request
from google_auth_oauthlib.flow import Flow, InstalledAppFlow
from config import Config
from google.oauth2 import service_account


main = Blueprint('main', __name__)




flow = Flow.from_client_secrets_file(
    Config.GOOGLE_CLIENT_SECRETS,
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
    # logging.debug('Handling callback...')
    flow.fetch_token(authorization_response=request.url)
    # logging.debug('Token fetched successfully')

    if session['state'] != request.args.get('state'):
        # logging.debug('State mismatch: Redirecting to index')
        return redirect(url_for('index'))

    credentials = flow.credentials
    session['credentials'] = credentials_to_dict(credentials)
    # logging.debug('Credentials saved to session')
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