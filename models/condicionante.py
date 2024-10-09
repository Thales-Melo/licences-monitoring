class Condicionante:
    def __init__(self, descricao, prazo=None, cumprida=False, tempo_restante=None, situacao=None, numero=None, tem_oficio=False, data_oficio=None, data_cumprimento=None):
        self.descricao = descricao
        self.prazo = prazo
        self.cumprida = cumprida
        self.tempo_restante = tempo_restante
        self.situacao = situacao
        self.numero = numero
        self.tem_oficio = tem_oficio
        self.data_oficio = data_oficio
        self.data_cumprimento = data_cumprimento

    def __repr__(self):
        return f"Condicionante(descricao='{self.descricao}', prazo='{self.prazo}', cumprida='{self.cumprida}', tempo_restante='{self.tempo_restante}', situacao='{self.situacao}', numero='{self.numero}', tem_oficio='{self.tem_oficio}', data_oficio='{self.data_oficio}', data_cumprimento='{self.data_cumprimento}')"

