import os
from dotenv import load_dotenv
from pymongo import MongoClient

# Carrega as variáveis de ambiente do arquivo .env, se existir
load_dotenv()

class Config:
    # Chave secreta para a aplicação Flask (busca da variável de ambiente)
    SECRET_KEY = os.getenv('SECRET_KEY')  # Usa uma variável de ambiente ou gera uma chave temporária

    # URI do MongoDB (busca da variável de ambiente)
    MONGO_URI = os.getenv('MONGO_URI')
    DATABASE_NAME = os.getenv('DATABASE_NAME')

    CLIENT = MongoClient(MONGO_URI)
    DB = CLIENT[DATABASE_NAME]
    DOCX_FILES_COLLECTION = DB['docx_files']

    # Diretório do script
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

    # Configurações do Google OAuth (busca das variáveis de ambiente ou usa caminho absoluto)
    GOOGLE_CLIENT_SECRETS = os.getenv('GOOGLE_CLIENT_SECRETS')
    REDIRECT_URI = os.getenv('REDIRECT_URI')

    # Configurações de logging e segurança (somente para desenvolvimento local)
    OAUTHLIB_INSECURE_TRANSPORT = os.getenv('OAUTHLIB_INSECURE_TRANSPORT')

    # Variáveis globais para controle dos arquivos
    ORDEM_NAO_ENTREGUES = 'asc'
    ORDEM_ENTREGUES = 'asc'
    ORDEM_ENCERRADOS = 'asc'

    CRITERIO_NAO_ENTREGUES = 'numero'
    CRITERIO_ENTREGUES = 'tempo_restante'
    CRITERIO_ENCERRADOS = 'numero'

    # Dicionários globais (ainda precisam ser manipulados dentro do código)
    ARQUIVOS_NAO_ENTREGUES = {}
    ARQUIVOS_ENTREGUES = {}
    ARQUIVOS_ENCERRADOS = {}

