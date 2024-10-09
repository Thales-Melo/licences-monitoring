# main/routes.py
import datetime
import logging
from flask import Blueprint, flash, redirect, render_template, url_for, session, request
from app.auth import credentials_to_dict
from app.utils import atualizar_situacao_condicionantes, carregar_dicionarios, enviar_email, salvar_dicionarios, executar_carregar_licencas, gerar_relatorio_excel, ordenar_arquivos, filtrar_e_ordenar, paginate, salvar_relatorio_mongodb, tempo_restante_condicionantes, update_order, listar_arquivos_pasta, parse_licenca, Licenca, calcula_tempo_restante, get_validade_em_dias, condicionantes_preenchidas, condicionantes_vencendo, verificar_se_oficio, encontrar_licenca_com_numero_de_processo
import google.oauth2.credentials
import googleapiclient.discovery
from datetime import datetime, timedelta

from config import Config
from google_auth_oauthlib.flow import Flow

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
        return redirect(url_for('main.index'))

    credentials = flow.credentials
    session['credentials'] = credentials_to_dict(credentials)
    # logging.debug('Credentials saved to session')
    return redirect(url_for('main.index'))


@main.route('/ordenar', methods=['GET'])
def ordenar():
    # Obtendo parâmetros da requisição
    criterio = request.args.get('criterio', 'numero')
    ordem = request.args.get('ordem', 'asc')
    search_query = request.args.get('search', '')
    tabela = request.args.get('tabela', 'nao_entregues')
    in_navigation = request.args.get('in_navigation', False)
    cor = request.args.get('cor', 'todas')

    # Página atual para cada tabela
    page_nao_entregues = int(request.args.get('page_nao_entregues', 1))
    page_entregues = int(request.args.get('page_entregues', 1))
    page_encerradas = int(request.args.get('page_encerradas', 1))

    # Atualiza a ordem global se não for uma navegação
    if in_navigation == 'false':
        update_order(tabela, criterio)

    # Carregar os arquivos novamente para garantir que temos os mais recentes
    carregar_dicionarios()

    # Ordena e filtra os arquivos
    arquivos_nao_entregues_filtered_sorted = filtrar_e_ordenar(Config.ARQUIVOS_NAO_ENTREGUES, Config.CRITERIO_NAO_ENTREGUES, Config.ORDEM_NAO_ENTREGUES, search_query)
    arquivos_entregues_filtered_sorted = filtrar_e_ordenar(Config.ARQUIVOS_ENTREGUES, Config.CRITERIO_ENTREGUES, Config.ORDEM_ENTREGUES, search_query, cor)
    arquivos_encerrados_filtered_sorted = filtrar_e_ordenar(Config.ARQUIVOS_ENCERRADOS, Config.CRITERIO_ENCERRADOS, Config.ORDEM_ENCERRADOS, search_query)

    # Paginação
    ITEMS_PER_PAGE = 10
    paginacao_nao_entregues_filtered = paginate(arquivos_nao_entregues_filtered_sorted, page_nao_entregues, ITEMS_PER_PAGE)
    paginacao_entregues_filtered = paginate(arquivos_entregues_filtered_sorted, page_entregues, ITEMS_PER_PAGE)
    paginacao_encerradas_filtered = paginate(arquivos_encerrados_filtered_sorted, page_encerradas, ITEMS_PER_PAGE)

    # Atualizar a sessão com a nova ordem e critério
    session['ordem'] = ordem
    session['NE_ordem'] = Config.ORDEM_NAO_ENTREGUES
    session['E_ordem'] = Config.ORDEM_ENTREGUES
    session['EN_ordem'] = Config.ORDEM_ENCERRADOS
    session['criterio'] = criterio
    session['NE_criterio'] = Config.CRITERIO_NAO_ENTREGUES
    session['E_criterio'] = Config.CRITERIO_ENTREGUES
    session['EN_criterio'] = Config.CRITERIO_ENCERRADOS

    # Renderizar a página com os arquivos ordenados e filtrados
    return render_template(
        'index.html',
        paginacao_nao_entregues=paginacao_nao_entregues_filtered,
        paginacao_entregues=paginacao_entregues_filtered,
        paginacao_encerradas=paginacao_encerradas_filtered,
        total_nao_entregues=len(arquivos_nao_entregues_filtered_sorted),
        total_entregues=len(arquivos_entregues_filtered_sorted),
        total_encerradas=len(arquivos_encerrados_filtered_sorted),
        page_nao_entregues=page_nao_entregues,
        page_entregues=page_entregues,
        page_encerradas=page_encerradas,
        ITEMS_PER_PAGE=ITEMS_PER_PAGE,
        criterio_ordenacao=criterio,
        ordem=ordem,
        cor=cor,
        search_query=search_query
    )



@main.route('/buscar', methods=['GET'])
def buscar():
# Buscar arquivos com base na consulta de busca
# Busca em todas as tabelas e ordena as tabelas com os critérios padrão (número para não entregues e arquivadas e tempo restante para entregues)
# Busca na tabela inteira e retorna um novo template com os resultados
    search_query = request.args.get('query', '')
    criterio_ordenacao = request.args.get('sort_by', 'numero')
    ordem = session.get('ordem', 'asc')

    # Filtra arquivos com base na consulta de busca
    def filter_by_search(arquivos):
        return {file_id: file_data for file_id, file_data in arquivos.items() if search_query.lower() in file_data['nome'].lower()}
    # Ordena arquivos antes de aplicar a busca
    nao_entregues_sorted = ordenar_arquivos(list(Config.ARQUIVOS_NAO_ENTREGUES.items()), criterio_ordenacao, ordem)
    entregues_sorted = ordenar_arquivos(list(Config.ARQUIVOS_ENTREGUES.items()), request.args.get('sort_by', 'tempo_restante'), ordem)
    encerradas_sorted = ordenar_arquivos(list(Config.ARQUIVOS_ENCERRADOS.items()), criterio_ordenacao, ordem)

    # Filtra e ordena arquivos filtrados
    arquivos_nao_entregues_filtered = filter_by_search(Config.ARQUIVOS_NAO_ENTREGUES)
    arquivos_entregues_filtered = filter_by_search(Config.ARQUIVOS_ENTREGUES)
    arquivos_encerrados_filtered = filter_by_search(Config.ARQUIVOS_ENCERRADOS)

    nao_entregues_filtered_sorted = ordenar_arquivos(list(arquivos_nao_entregues_filtered.items()), criterio_ordenacao, ordem)
    entregues_filtered_sorted = ordenar_arquivos(list(arquivos_entregues_filtered.items()), request.args.get('sort_by', 'tempo_restante'), ordem)
    encerradas_filtered_sorted = ordenar_arquivos(list(arquivos_encerrados_filtered.items()), criterio_ordenacao, ordem)

    # Paginação
    page_nao_entregues = int(request.args.get('page_nao_entregues', 1))
    page_entregues = int(request.args.get('page_entregues', 1))
    page_encerradas = int(request.args.get('page_encerradas', 1))

    ITEMS_PER_PAGE = 10

    def paginate(items, page):
        start = (page - 1) * ITEMS_PER_PAGE
        end = start + ITEMS_PER_PAGE
        return items[start:end]
    
    total_nao_entregues = len(nao_entregues_sorted)
    total_entregues = len(entregues_sorted)
    total_encerradas = len(encerradas_sorted)

    paginacao_nao_entregues = paginate(nao_entregues_sorted, page_nao_entregues)
    paginacao_entregues = paginate(entregues_sorted, page_entregues)
    paginacao_encerradas = paginate(encerradas_sorted, page_encerradas)

    total_nao_entregues_filtered = len(nao_entregues_filtered_sorted)
    total_entregues_filtered = len(entregues_filtered_sorted)
    total_encerradas_filtered = len(encerradas_filtered_sorted)

    paginacao_nao_entregues_filtered = paginate(nao_entregues_filtered_sorted, page_nao_entregues)
    paginacao_entregues_filtered = paginate(entregues_filtered_sorted, page_entregues)
    paginacao_encerradas_filtered = paginate(encerradas_filtered_sorted, page_encerradas)

    return render_template(
        'index.html',
        paginacao_nao_entregues=paginacao_nao_entregues_filtered,
        paginacao_entregues=paginacao_entregues_filtered,
        paginacao_encerradas=paginacao_encerradas_filtered,
        total_nao_entregues=total_nao_entregues,
        total_entregues=total_entregues,
        total_encerradas=total_encerradas,
        paginacao_nao_entregues_filtered=paginacao_nao_entregues_filtered,
        paginacao_entregues_filtered=paginacao_entregues_filtered,
        paginacao_encerradas_filtered=paginacao_encerradas_filtered,
        total_nao_entregues_filtered=total_nao_entregues_filtered,
        total_entregues_filtered=total_entregues_filtered,
        total_encerradas_filtered=total_encerradas_filtered,
        page_nao_entregues=page_nao_entregues,
        page_entregues=page_entregues,
        page_encerradas=page_encerradas,
        ITEMS_PER_PAGE=ITEMS_PER_PAGE,
        criterio_ordenacao=criterio_ordenacao,
        ordem=ordem,
        search_query=search_query
    )

@main.route('/atualizar', methods=['POST'])
def atualizar():
    if 'credentials' not in session:
        return redirect(url_for('main.authorize'))

    # Carregar dicionários
    carregar_dicionarios()

    credentials = google.oauth2.credentials.Credentials(**session['credentials'])
    drive_service = googleapiclient.discovery.build('drive', 'v3', credentials=credentials)

    # Buscar arquivos do Google Drive
    pasta_virtual_id = '1q-Z80IpvGmS9tWQj6TeshWmpYAOrDxr7'  # Substitua pelo ID da pasta

    files = listar_arquivos_pasta(drive_service, pasta_virtual_id)

    ids_existentes = set(Config.ARQUIVOS_NAO_ENTREGUES) | set(Config.ARQUIVOS_ENTREGUES) | set(Config.ARQUIVOS_ENCERRADOS)
    novos_arquivos = []

    for file in files:
        if file['name'].endswith('.docx') and 'OF' not in file['name']:
            if file['id'] not in ids_existentes:
                nome_parts = file['name'].split(' - ')
                if len(nome_parts) == 3:
                    numero, tipo, nome = nome_parts
                else:
                    numero, tipo, nome = "N/A", "N/A", file['name']
                Config.ARQUIVOS_NAO_ENTREGUES[file['id']] = {
                    'numero': numero.strip(),
                    'tipo': tipo.strip(),
                    'nome': nome.strip(),
                    'numero_processo': "N/A",
                    'data_carimbo': "N/A",
                    'tempo_restante': "N/A",
                    'prazo_renovacao': "N/A",
                    'data_renovacao': "N/A",
                    'data_arquivada': "N/A",
                    'data_vencimento': "N/A",
                    'condicionantes_verify': "incompletas",
                    'situacao_condicionantes': "N/A",
                    'eh_oficio_entregue': False,
                    'data': None
                }
                novos_arquivos.append(file['name'])

    if novos_arquivos:
        salvar_dicionarios()
        logging.info(f'Novos arquivos encontrados e adicionados: {novos_arquivos}')
    else:
        logging.info('Nenhum novo arquivo encontrado.')

    return redirect(url_for('main.index'))


# Rota que filtra por cor
@main.route('/filtrar_por_cor', methods=['GET'])
def filtrar_por_cor():
    cor = request.args.get('cor', 'vermelho')
    criterio_ordenacao = request.args.get('sort_by', 'numero')
    ordem = session.get('ordem', 'asc')

    # Filtra arquivos com base na cor
    def filter_by_color(arquivos):
        return {file_id: file_data for file_id, file_data in arquivos.items() if file_data['situacao_condicionantes'] == cor}

    # Ordena arquivos antes de aplicar a busca
    nao_entregues_sorted = ordenar_arquivos(list(Config.ARQUIVOS_NAO_ENTREGUES.items()), criterio_ordenacao, ordem)
    entregues_sorted = ordenar_arquivos(list(Config.ARQUIVOS_ENTREGUES.items()), request.args.get('sort_by', 'tempo_restante'), ordem)
    encerradas_sorted = ordenar_arquivos(list(Config.ARQUIVOS_ENCERRADOS.items()), criterio_ordenacao, ordem)

    # Filtra e ordena arquivos filtrados
    arquivos_nao_entregues_filtered = Config.ARQUIVOS_NAO_ENTREGUES
    arquivos_entregues_filtered = filter_by_color(Config.ARQUIVOS_ENTREGUES)
    arquivos_encerrados_filtered = Config.ARQUIVOS_ENCERRADOS

    nao_entregues_filtered_sorted = ordenar_arquivos(list(arquivos_nao_entregues_filtered.items()), criterio_ordenacao, ordem)
    entregues_filtered_sorted = ordenar_arquivos(list(arquivos_entregues_filtered.items()), request.args.get('sort_by', 'tempo_restante'), ordem)
    encerradas_filtered_sorted = ordenar_arquivos(list(arquivos_encerrados_filtered.items()), criterio_ordenacao, ordem)

    # Paginação
    page_nao_entregues = int(request.args.get('page_nao_entregues', 1))
    page_entregues = int(request.args.get('page_entregues', 1))
    page_encerradas = int(request.args.get('page_encerradas', 1))

    ITEMS_PER_PAGE = 10

    def paginate(items, page):
        start = (page - 1) * ITEMS_PER_PAGE
        end = start + ITEMS_PER_PAGE
        return items[start:end]

    total_nao_entregues = len(nao_entregues_sorted)
    total_entregues = len(entregues_sorted)
    total_encerradas = len(encerradas_sorted)

    paginacao_nao_entregues = paginate(nao_entregues_sorted, page_nao_entregues)
    paginacao_entregues = paginate(entregues_sorted, page_entregues)
    paginacao_encerradas = paginate(encerradas_sorted, page_encerradas)

    total_nao_entregues_filtered = len(nao_entregues_filtered_sorted)
    total_entregues_filtered = len(entregues_filtered_sorted)
    total_encerradas_filtered = len(encerradas_filtered_sorted)

    paginacao_nao_entregues_filtered = paginate(nao_entregues_filtered_sorted, page_nao_entregues)
    paginacao_entregues_filtered = paginate(entregues_filtered_sorted, page_entregues)
    paginacao_encerradas_filtered = paginate(encerradas_filtered_sorted, page_encerradas)

    return render_template(
        'index.html',
        paginacao_nao_entregues=paginacao_nao_entregues_filtered,
        paginacao_entregues=paginacao_entregues_filtered,
        paginacao_encerradas=paginacao_encerradas_filtered,
        total_nao_entregues=total_nao_entregues,
        total_entregues=total_entregues,
        total_encerradas=total_encerradas,
        paginacao_nao_entregues_filtered=paginacao_nao_entregues_filtered,
        paginacao_entregues_filtered=paginacao_entregues_filtered,
        paginacao_encerradas_filtered=paginacao_encerradas_filtered,
        total_nao_entregues_filtered=total_nao_entregues_filtered,
        total_entregues_filtered=total_entregues_filtered,
        total_encerradas_filtered=total_encerradas_filtered,
        page_nao_entregues=page_nao_entregues,
        page_entregues=page_entregues,
        page_encerradas=page_encerradas,
        ITEMS_PER_PAGE=ITEMS_PER_PAGE,
        criterio_ordenacao=criterio_ordenacao,
        ordem=ordem,
        search_query=''
    )

@main.route('/')
def index():

    if 'credentials' not in session:
        return redirect(url_for('main.authorize'))

    salvar_dicionarios()
    carregar_dicionarios()

    # Inicializa variáveis se não estiverem definidas
    # if 'Config.ARQUIVOS_NAO_ENTREGUES' not in globals():
    #     print("não tava definido")
    #     Config.ARQUIVOS_NAO_ENTREGUES = {}
    # if 'Config.ARQUIVOS_ENTREGUES' not in globals():
    #     Config.ARQUIVOS_ENTREGUES = {}
    # if 'Config.ARQUIVOS_ENCERRADOS' not in globals():
    #     Config.ARQUIVOS_ENCERRADOS = {}

    # Resto do código
    credentials = google.oauth2.credentials.Credentials(**session['credentials'])
    drive_service = googleapiclient.discovery.build('drive', 'v3', credentials=credentials)
    pasta_virtual_id = '1eq9AR9NEuo3fTFBw3JPPa9vxLSXkzGJY'
    files = listar_arquivos_pasta(drive_service, pasta_virtual_id)

    print("arquivos que já tem")
    for file_id, file_data in Config.ARQUIVOS_NAO_ENTREGUES.items():
        print(file_data['nome'])
        print(file_id)

    print("______________________")
    for file_id, file_data in Config.ARQUIVOS_ENTREGUES.items():
        print(file_data['nome'])
        print(file_id)

    print("______________________")

    for file in files:
        print(file['name'])
        print(file['id'])
        if file['name'].endswith('.docx'):
            if file['id'] not in Config.ARQUIVOS_NAO_ENTREGUES and file['id'] not in Config.ARQUIVOS_ENTREGUES and file['id'] not in Config.ARQUIVOS_ENCERRADOS:   
                print("\nArquivo não encontrado")
                print(file['name'])
                print(file['id'])
                # iterar sobre todos os dicionarios de arquivos e verificar se tem o mesmo numero de processo
                # 

                Config.ARQUIVOS_NAO_ENTREGUES[file['id']] = {
                    'numero': "N/A",
                    'tipo': "N/A",
                    'nome': "N/A",
                    'numero_processo': "N/A",
                    'data_carimbo': "N/A",
                    'tempo_restante': "N/A",
                    'prazo_renovacao': "N/A",
                    'data_renovacao': "N/A",
                    'data_arquivada': "N/A",
                    'data_vencimento': "N/A",
                    'condicionantes_verify': "incompletas",
                    'situacao_condicionantes': "N/A",
                    'eh_oficio_entregue': False,
                    'data': None
                }
                # print(Config.ARQUIVOS_NAO_ENTREGUES[file['id']])


    executar_carregar_licencas()
    salvar_dicionarios()
    # for file_id, file_data in Config.ARQUIVOS_NAO_ENTREGUES.items():
    #     licenca = parse_licenca(file_data.get('data'))
    #     if licenca and isinstance(licenca, Licenca):
    #         file_data['numero_processo'] = licenca.numero_processo
    #         print("Numero do processo: ", licenca.numero_processo)
    #         print("Nome: ", licenca.requerente)
    #     else:
    #         print("Erro ao carregar o número do processo")

    # Cria uma lista para armazenar os IDs dos arquivos que precisam ser movidos
    arquivos_para_mover = []

    for file_id, file_data in Config.ARQUIVOS_ENTREGUES.items():
        licenca = parse_licenca(file_data.get('data'))
        if licenca and isinstance(licenca, Licenca):
            tempo_restante = calcula_tempo_restante(licenca)
            file_data['tempo_restante'] = tempo_restante
            file_data['prazo_renovacao'] = tempo_restante - 120 if tempo_restante is not None else "N/A"
            validade_em_dias = get_validade_em_dias(licenca.validade)
            data_validade = datetime.strptime(licenca.data_carimbo + " 00:00:00", '%d/%m/%Y %H:%M:%S') + timedelta(days=validade_em_dias) if validade_em_dias is not None else None
            file_data['data_renovacao'] = (data_validade - timedelta(days=120)).strftime('%d/%m/%Y') if data_validade is not None else "N/A"
            file_data['data_vencimento'] = data_validade.strftime('%d/%m/%Y') if data_validade is not None else "N/A"
            file_data['data_carimbo'] = licenca.data_carimbo
            file_data['numero_processo'] = licenca.numero_processo
            file_data['numero'] = licenca.numero

            if condicionantes_preenchidas(file_id) == 'False':
                file_data['condicionantes_verify'] = "INCOMPLETAS"
                # print("\n")
            else:
                file_data['condicionantes_verify'] = "COMPLETAS"
                file_data['situacao_condicionantes'] = condicionantes_vencendo(file_id)
                if file_data['situacao_condicionantes'] == 'concluida':
                    arquivos_para_mover.append(file_id)
                    # salvar a data que a licença foi arquivada
                    file_data['data_arquivada'] = datetime.now().strftime('%d/%m/%Y')
            # print("\n")

    # Agora processa a lista de IDs para mover os arquivos
    for file_id in arquivos_para_mover:
        Config.ARQUIVOS_ENCERRADOS[file_id] = Config.ARQUIVOS_ENTREGUES.pop(file_id)

    for file_id, file_data in Config.ARQUIVOS_NAO_ENTREGUES.items():
        licenca = parse_licenca(file_data.get('data'))
        # licenca.numero .get('numero') numero
        if licenca and isinstance(licenca, Licenca):
            # file_data['numero'] = licenca.numero
            # print(file_data['numero'])
            if condicionantes_preenchidas(file_id) == 'False':
                file_data['condicionantes_verify'] = "INCOMPLETAS"
                # print("Condicionantes não preenchidas 2\n")
            else:
                file_data['condicionantes_verify'] = "COMPLETAS"
                # print("Condicionantes preenchidas\n")

    salvar_dicionarios()
    # print()
    # Obtém o critério de ordenação, a ordem e a consulta de busca da URL
    criterio_ordenacao = request.args.get('sort_by', 'numero')
    ordem = session.get('ordem', 'asc')
    search_query = request.args.get('search', '')

    # Filtra arquivos com base na consulta de busca
    def filter_by_search(arquivos):
        return {file_id: file_data for file_id, file_data in arquivos.items() if search_query.lower() in file_data['nome'].lower()}

    # Ordena arquivos antes de aplicar a busca
    nao_entregues_sorted = ordenar_arquivos(list(Config.ARQUIVOS_NAO_ENTREGUES.items()), criterio_ordenacao, ordem)
    entregues_sorted = ordenar_arquivos(list(Config.ARQUIVOS_ENTREGUES.items()), request.args.get('sort_by', 'tempo_restante'), ordem)
    encerradas_sorted = ordenar_arquivos(list(Config.ARQUIVOS_ENCERRADOS.items()), criterio_ordenacao, ordem)

    # Filtra e ordena arquivos filtrados
    arquivos_nao_entregues_filtered = filter_by_search(Config.ARQUIVOS_NAO_ENTREGUES)
    arquivos_entregues_filtered = filter_by_search(Config.ARQUIVOS_ENTREGUES)
    arquivos_encerrados_filtered = filter_by_search(Config.ARQUIVOS_ENCERRADOS)

    nao_entregues_filtered_sorted = ordenar_arquivos(list(arquivos_nao_entregues_filtered.items()), criterio_ordenacao, ordem)
    entregues_filtered_sorted = ordenar_arquivos(list(arquivos_entregues_filtered.items()), request.args.get('sort_by', 'tempo_restante'), ordem)
    encerradas_filtered_sorted = ordenar_arquivos(list(arquivos_encerrados_filtered.items()), criterio_ordenacao, ordem)

    # Paginação
    page_nao_entregues = int(request.args.get('page_nao_entregues', 1))
    page_entregues = int(request.args.get('page_entregues', 1))
    page_encerradas = int(request.args.get('page_encerradas', 1))

    ITEMS_PER_PAGE = 10

    def paginate(items, page):
        start = (page - 1) * ITEMS_PER_PAGE
        end = start + ITEMS_PER_PAGE
        return items[start:end]

    total_nao_entregues = len(nao_entregues_sorted)
    total_entregues = len(entregues_sorted)
    total_encerradas = len(encerradas_sorted)

    paginacao_nao_entregues = paginate(nao_entregues_sorted, page_nao_entregues)
    paginacao_entregues = paginate(entregues_sorted, page_entregues)
    paginacao_encerradas = paginate(encerradas_sorted, page_encerradas)

    total_nao_entregues_filtered = len(nao_entregues_filtered_sorted)
    total_entregues_filtered = len(entregues_filtered_sorted)
    total_encerradas_filtered = len(encerradas_filtered_sorted)

    paginacao_nao_entregues_filtered = paginate(nao_entregues_filtered_sorted, page_nao_entregues)
    paginacao_entregues_filtered = paginate(entregues_filtered_sorted, page_entregues)
    paginacao_encerradas_filtered = paginate(encerradas_filtered_sorted, page_encerradas)

    return render_template(
        'index.html',
        paginacao_nao_entregues=paginacao_nao_entregues,
        paginacao_entregues=paginacao_entregues,
        paginacao_encerradas=paginacao_encerradas,
        total_nao_entregues=total_nao_entregues,
        total_entregues=total_entregues,
        total_encerradas=total_encerradas,
        paginacao_nao_entregues_filtered=paginacao_nao_entregues_filtered,
        paginacao_entregues_filtered=paginacao_entregues_filtered,
        paginacao_encerradas_filtered=paginacao_encerradas_filtered,
        total_nao_entregues_filtered=total_nao_entregues_filtered,
        total_entregues_filtered=total_entregues_filtered,
        total_encerradas_filtered=total_encerradas_filtered,
        page_nao_entregues=page_nao_entregues,
        page_entregues=page_entregues,
        page_encerradas=page_encerradas,
        ITEMS_PER_PAGE=ITEMS_PER_PAGE,
        criterio_ordenacao=criterio_ordenacao,
        ordem=ordem,
        search_query=search_query  # Passa o valor da busca para o template
    )


@main.route('/mover_arquivo/<file_id>', methods=['POST'])
def mover_arquivo(file_id):
    salvar_dicionarios()
    
    if (verificar_se_oficio(file_id)):
        # Atualiza a licença correspondente com as condicionantes do ofício
        licenca_original_id = encontrar_licenca_com_numero_de_processo(Config.ARQUIVOS_NAO_ENTREGUES[file_id]['numero_processo'])
        if licenca_original_id is not None:
            licenca_original = parse_licenca(Config.ARQUIVOS_ENTREGUES[licenca_original_id]['data'])
            if licenca_original is not None and isinstance(licenca_original, Licenca):
                # Atualiza a licença com as condicionantes do ofício
                licenca_copia = licenca_original.copiar()
                oficio = parse_licenca(Config.ARQUIVOS_NAO_ENTREGUES[file_id]['data'])
                if oficio is not None and isinstance(oficio, Licenca):
                    for cond in oficio.condicionantes:
                        for cond2 in licenca_copia.condicionantes:
                            if cond2.numero.lstrip('0') == cond.numero.lstrip('0'):
                                cond2.tem_oficio = True
                                cond2.descricao = cond.descricao
                                cond2.prazo = cond.prazo
                                cond2.data_oficio = request.form.get('data_carimbo')
                                break
                    Config.ARQUIVOS_ENTREGUES[licenca_original_id]['data'] = repr(licenca_copia)              
                        
            else:
                print("Erro ao mover arquivo: Licença não encontrada")
        else:
            print("Erro ao mover arquivo: Licença não encontrada")

            
        Config.ARQUIVOS_NAO_ENTREGUES[file_id]['eh_oficio_entregue'] = True
        salvar_dicionarios()
        return redirect(url_for('main.index'))


    if file_id in Config.ARQUIVOS_NAO_ENTREGUES:
        # Verifica se as condicionantes estão completas
        if Config.ARQUIVOS_NAO_ENTREGUES[file_id].get('condicionantes_verify') == "COMPLETAS":
            data_carimbo = request.form.get('data_carimbo')
            if data_carimbo:
                # Adiciona o arquivo ao dicionário de entregues
                Config.ARQUIVOS_NAO_ENTREGUES[file_id]['data_carimbo'] = datetime.strptime(data_carimbo + " 00:00:00", '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')
                
                # Atualiza o atributo data_carimbo da licença
                licenca = parse_licenca(Config.ARQUIVOS_NAO_ENTREGUES[file_id]['data'])
                if licenca is not None and isinstance(licenca, Licenca):
                    # Move o arquivo para o dicionário de entregues
                    Config.ARQUIVOS_ENTREGUES[file_id] = Config.ARQUIVOS_NAO_ENTREGUES.pop(file_id)
                    salvar_dicionarios()
                    # Atualiza os atributos da licença
                    licenca.data_carimbo = datetime.strptime(data_carimbo, '%Y-%m-%d').strftime('%d/%m/%Y')
                    licenca.tempo_restante = calcula_tempo_restante(licenca)
                    Config.ARQUIVOS_ENTREGUES[file_id]['tempo_restante'] = licenca.tempo_restante
                    licenca.prazo_renovacao = licenca.tempo_restante - 120 if licenca.tempo_restante is not None else "N/A"
                    licenca.data_renovacao = (datetime.strptime(data_carimbo, '%Y-%m-%d') + timedelta(days=licenca.prazo_renovacao)).strftime('%d/%m/%Y') if licenca.tempo_restante is not None else "N/A"
                    licenca.data_vencimento = (datetime.strptime(data_carimbo, '%Y-%m-%d') + timedelta(days=licenca.tempo_restante)).strftime('%d/%m/%Y') if licenca.tempo_restante is not None else "N/A"
                    Config.ARQUIVOS_ENTREGUES[file_id]['prazo_renovacao'] = licenca.prazo_renovacao
                    Config.ARQUIVOS_ENTREGUES[file_id]['data_renovacao'] = licenca.data_renovacao
                    Config.ARQUIVOS_ENTREGUES[file_id]['data_vencimento'] = licenca.data_vencimento
                    Config.ARQUIVOS_ENTREGUES[file_id]['data'] = repr(licenca)

                else:
                    print("Erro ao carimbar arquivo: Faça novamente")
                salvar_dicionarios()
        else:
            # Adiciona uma mensagem flash para exibir no front-end
            flash("Preencha o campo 'PRAZO' de todas as condicionantes antes de enviar a licença para monitoramento.", "warning")
    
    salvar_dicionarios()
    carregar_dicionarios()
    return redirect(url_for('main.index'))


@main.route('/descarimbar_arquivo/<file_id>', methods=['POST'])
def descarimbar_arquivo(file_id):
    if file_id in Config.ARQUIVOS_ENTREGUES:
        # Atualiza o valor de data_carimbo e move o arquivo para 'nao_entregues'
        Config.ARQUIVOS_ENTREGUES[file_id]['data_carimbo'] = "N/A"
        
        # Remove do banco de dados a entrada em "entregues"
        Config.DB.entregues.delete_one({'_id': file_id})
        
        # Adiciona à lista "nao_entregues" e atualiza no banco de dados
        Config.ARQUIVOS_NAO_ENTREGUES[file_id] = Config.ARQUIVOS_ENTREGUES.pop(file_id)
        Config.DB.nao_entregues.update_one({'_id': file_id}, {'$set': Config.ARQUIVOS_NAO_ENTREGUES[file_id]}, upsert=True)
        
        # Chama salvar_dicionarios e carregar_dicionarios para garantir que tudo seja atualizado
        salvar_dicionarios()
        carregar_dicionarios()
    
    return redirect(url_for('main.index'))


@main.route('/encerrar/<file_id>', methods=['POST'])
def encerrar(file_id):
    if file_id in Config.ARQUIVOS_ENTREGUES:
        try:
            Config.ARQUIVOS_ENCERRADOS[file_id] = Config.ARQUIVOS_ENTREGUES.pop(file_id)
            # salvar a data que a licença foi arquivada
            Config.ARQUIVOS_ENCERRADOS[file_id]['data_arquivada'] = datetime.now().strftime('%d/%m/%Y')
            salvar_dicionarios()
        except Exception as e:
            logging.error(f"Erro ao encerrar o arquivo {file_id}: {e}")
    return redirect(url_for('main.index'))

@main.route('/retomar/<file_id>', methods=['POST'])
def retomar(file_id):
    if file_id in Config.ARQUIVOS_ENCERRADOS:
        Config.ARQUIVOS_ENTREGUES[file_id] = Config.ARQUIVOS_ENCERRADOS.pop(file_id)
        salvar_dicionarios()
    return redirect(url_for('main.index'))


@main.route('/detalhes/<file_id>')
def detalhes(file_id):
    # logging.debug(f'Retrieving details for file_id: {file_id}')
    # tipo_tabela = request.args.get('tipo_tabela', 'nao_entregues')
    # Recupera a licença do dicionário
    licenca_string = Config.ARQUIVOS_NAO_ENTREGUES.get(file_id, {}).get('data') or Config.ARQUIVOS_ENTREGUES.get(file_id, {}).get('data') or Config.ARQUIVOS_ENCERRADOS.get(file_id, {}).get('data')
    
    # Processa a licença se licenca_string for uma string
    licenca = parse_licenca(licenca_string) if isinstance(licenca_string, str) else licenca_string
    # if licenca is None:
        # logging.debug(f'No data found for file_id: {file_id}')
    tipo_tabela = ''
    # Atualizar o tempo restante para cumprir as condicionantes
    licenca.condicionantes = tempo_restante_condicionantes(licenca, file_id)
    licenca.condicionantes = atualizar_situacao_condicionantes(licenca)
    if file_id in Config.ARQUIVOS_NAO_ENTREGUES:
        Config.ARQUIVOS_NAO_ENTREGUES[file_id]['data'] = repr(licenca)
        tipo_tabela = 'nao_entregues'
    elif file_id in Config.ARQUIVOS_ENTREGUES:
        Config.ARQUIVOS_ENTREGUES[file_id]['data'] = repr(licenca)
        tipo_tabela = 'entregues'
    elif file_id in Config.ARQUIVOS_ENCERRADOS:
        Config.ARQUIVOS_ENCERRADOS[file_id]['data'] = repr(licenca)
        tipo_tabela = 'encerrados'

    salvar_dicionarios()
    # for cond in licenca.condicionantes:
    #     print(cond.descricao)
    #     print(cond.prazo)
    #     print(cond.cumprida)
    #     print(cond.tempo_restante)
    #     print()
    # Recupera o nome do arquivo de ambos os dicionários, preferindo Config.ARQUIVOS_NAO_ENTREGUES
    numero_licenca = Config.ARQUIVOS_NAO_ENTREGUES.get(file_id, {}).get('numero') or Config.ARQUIVOS_ENTREGUES.get(file_id, {}).get('numero') or Config.ARQUIVOS_ENCERRADOS.get(file_id, {}).get('numero')
    tipo_licenca = Config.ARQUIVOS_NAO_ENTREGUES.get(file_id, {}).get('tipo') or Config.ARQUIVOS_ENTREGUES.get(file_id, {}).get('tipo') or Config.ARQUIVOS_ENCERRADOS.get(file_id, {}).get('tipo')

    # Renderiza o template com a licença
    return render_template('detalhes.html', licenca=licenca, numero_licenca=numero_licenca, tipo_licenca=tipo_licenca, file_id=file_id, tipo_tabela=tipo_tabela)


@main.route('/cumprir_condicionante', methods=['POST'])
def cumprir_condicionante():
    file_id = request.form.get('file_id')
    cond_index_str = request.form.get('cond_index')
    cond_index = int(cond_index_str) - 1  # Índice da condicionante
    licenca_string =Config.ARQUIVOS_ENTREGUES.get(file_id, {}).get('data')
    licenca = parse_licenca(licenca_string) if isinstance(licenca_string, str) else licenca_string
    
    if licenca:
        condicionante = licenca.condicionantes[cond_index]
        condicionante.cumprida = True
        condicionante.data_cumprimento = datetime.now().strftime('%d/%m/%Y')

        Config.ARQUIVOS_ENTREGUES[file_id]['data'] = repr(licenca)

    salvar_dicionarios()
    carregar_dicionarios()

    return redirect(url_for('main.detalhes', file_id=file_id))


@main.route('/atualizar_prazo', methods=['POST'])
def atualizar_prazo():
    file_id = request.form.get('file_id')
    cond_index_str = request.form.get('cond_index')
    # print("cond_index=", cond_index_str)                                                             
    # print("file_id=", file_id)
    # Verifica se cond_index está presente e é um número válido
    if cond_index_str is None or not cond_index_str.isdigit():
        return "Índice da condicionante inválido", 400

    cond_index = int(cond_index_str) - 1  # Índice da condicionante
    
    tipo_prazo = request.form.get(f'tipo_prazo')
    quantidade_prazo_str = request.form.get(f'quantidade_prazo')
    
    # Verifica se quantidade_prazo está presente e é um número válido
    if quantidade_prazo_str is None or not quantidade_prazo_str.isdigit():
        quantidade_prazo = 0  # Ou qualquer valor padrão apropriado
    else:
        quantidade_prazo = int(quantidade_prazo_str)

    # Recuperar a licença e a condicionante
    licenca_string = Config.ARQUIVOS_NAO_ENTREGUES.get(file_id, {}).get('data') or Config.ARQUIVOS_ENTREGUES.get(file_id, {}).get('data')
    licenca = parse_licenca(licenca_string)

    # print("tamanho da lista de condicionantes: ", len(licenca.condicionantes))

    if licenca is None or cond_index >= len(licenca.condicionantes):
        return "Licença ou condicionante não encontrada", 404

    # print("tipo_prazo = ", tipo_prazo)
    # print("quantidade_prazo = ", quantidade_prazo)

    # Atualizar o prazo com base no tipo selecionado
    if tipo_prazo == 'dias':
        licenca.condicionantes[cond_index].prazo = f"{quantidade_prazo} dias a partir do carimbo"
    elif tipo_prazo == 'meses':
        licenca.condicionantes[cond_index].prazo = f"{quantidade_prazo} meses a partir do carimbo"
    elif tipo_prazo == 'anos':
        licenca.condicionantes[cond_index].prazo = f"{quantidade_prazo} anos a partir do carimbo"
    elif tipo_prazo == 'intervalado':
        licenca.condicionantes[cond_index].prazo = f"Intervalado ({quantidade_prazo} meses)"
    else:
        return "Tipo de prazo inválido", 400


    # Aqui você deve salvar a licença atualizada no JSON ou banco de dados
    # Atualize o atributo 'data' da licença no dicionário correspondente
    if file_id in Config.ARQUIVOS_NAO_ENTREGUES:
        Config.ARQUIVOS_NAO_ENTREGUES[file_id]['data'] = repr(licenca)
    elif file_id in Config.ARQUIVOS_ENTREGUES:
        Config.ARQUIVOS_ENTREGUES[file_id]['data'] = repr(licenca)
    elif file_id in Config.ARQUIVOS_ENCERRADOS:
        Config.ARQUIVOS_ENCERRADOS[file_id]['data'] = repr(licenca)
    

    salvar_dicionarios()


    return redirect(url_for('main.detalhes', file_id=file_id))


@main.route('/enviar_relatorio', methods=['POST'])
def enviar_relatorio():
    # Gerar o relatório em formato Excel
    relatorio_df = gerar_relatorio_excel()
    
    # Salvar o relatório no MongoDB
    salvar_relatorio_mongodb(relatorio_df)

    # Enviar o e-mail com o relatório extraído do MongoDB
    enviar_email()
    
    return redirect(url_for('main.index'))