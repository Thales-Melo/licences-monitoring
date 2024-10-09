from threading import Thread
from app import create_app, schedule_secret_key_update, update_secret_key
from app.utils import carregar_dicionarios, executar_carregar_licencas

# Cria o aplicativo Flask
app = create_app()

# Carrega as licenças no início
executar_carregar_licencas()

# Tente carregar os dicionários após a inicialização do app
try:
    carregar_dicionarios()  # Agora deve funcionar corretamente
    print("Dicionários carregados com sucesso.")
except Exception as e:
    print(f"Erro ao carregar dicionários no início: {e}")

# Atualiza a chave secreta imediatamente ao iniciar
update_secret_key(app)

# Inicia o agendamento em um thread separado para não bloquear o app
scheduler_thread = Thread(target=schedule_secret_key_update, args=(app,))
scheduler_thread.daemon = True
scheduler_thread.start()

# Remova ou comente esta linha para evitar execução direta
# if __name__ == '__main__':
#     app.run(debug=True)
