from werkzeug.exceptions import Forbidden


def storage_resource(database: str, subject: str, verify_insert: bool=False, key_fields: str=None):
    """
    Decorator responsável por definir o assunto e os campos chaves de uma coleção de dados

    :param database: Identificação do banco de dados de destino
    :param subject: Assunto da coleção de dados
    :param verify_insert: Indica se verifica a existencia de dados no insert
    :param key_fields: Campos chave da coleção de dados (para verificação de existência)
    """

    def decorator(cls):
        setattr(cls, 'subject', subject)
        setattr(cls, 'database', database)
        setattr(cls, 'verify_insert', verify_insert)

        list_key_fields = key_fields.split(',') if key_fields else None
        if list_key_fields and '_id' in list_key_fields:
            raise Forbidden('Campo reservado "_id" não pode fazer parte dos campos chave')
        setattr(cls, 'key_fields', list_key_fields)
        return cls

    return decorator
