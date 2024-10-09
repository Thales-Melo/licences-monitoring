from datetime import datetime

class Licenca:
    def __init__(self, numero, tipo, requerente, cnpj, numero_processo, endereco, atividade, classe, porte, potencial_poluidor, coordenadas, validade, condicionantes, data_carimbo=None, tempo_restante=None, prazo_renovacao=None, data_renovacao=None, data_vencimento=None):
        self.numero = numero
        self.tipo = tipo
        self.requerente = requerente
        self.cnpj = cnpj
        self.numero_processo = numero_processo
        self.endereco = endereco
        self.atividade = atividade
        self.classe = classe
        self.porte = porte
        self.potencial_poluidor = potencial_poluidor
        self.coordenadas = coordenadas
        self.validade = validade
        self.condicionantes = condicionantes
        self.data_carimbo = data_carimbo if data_carimbo else datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        self.tempo_restante = tempo_restante if tempo_restante else None
        self.prazo_renovacao = prazo_renovacao if prazo_renovacao else None
        self.data_renovacao = data_renovacao if data_renovacao else None
        self.data_vencimento = data_vencimento if data_vencimento else None
        
    def __repr__(self):
        return (f"Licenca(numero='{self.numero}', tipo='{self.tipo}', requerente='{self.requerente}', cnpj='{self.cnpj}', "
                f"numero_processo='{self.numero_processo}', endereco='{self.endereco}', atividade='{self.atividade}', classe='{self.classe}', "
                f"porte='{self.porte}', potencial_poluidor='{self.potencial_poluidor}', "
                f"coordenadas='{self.coordenadas}', validade='{self.validade}', data_carimbo='{self.data_carimbo}', "
                f"condicionantes={self.condicionantes})")

    def copiar(self):
        """Copia os atributos da licença atual e retorna uma nova instância de Licenca."""
        return Licenca(
            numero=self.numero,
            tipo=self.tipo,
            requerente=self.requerente,
            cnpj=self.cnpj,
            numero_processo=self.numero_processo,
            endereco=self.endereco,
            atividade=self.atividade,
            classe=self.classe,
            porte=self.porte,
            potencial_poluidor=self.potencial_poluidor,
            coordenadas=self.coordenadas,
            validade=self.validade,
            condicionantes=self.condicionantes,
            data_carimbo=self.data_carimbo,
            tempo_restante=self.tempo_restante,
            prazo_renovacao=self.prazo_renovacao,
            data_renovacao=self.data_renovacao,
            data_vencimento=self.data_vencimento
        )
    
    def condicionantes_unique(self):
        # confere se na lista de condicionantes há condicionantes repetidos
        # se tiver, remove

        # cria uma lista vazia para armazenar os condicionantes únicos
        cond_unique = []
        # percorre a lista de condicionantes da licença
        for cond in self.condicionantes:
            # se o condicionante não estiver na lista de cond_unique (verificar com base no número da condicionante)
            if not any(cond.numero == c.numero for c in cond_unique):
                # adiciona o condicionante à lista de cond_unique
                cond_unique.append(cond)
            
        # retorna a lista de condicionantes únicos
        return cond_unique
