from builtins import list
from bson import ObjectId
from werkzeug.exceptions import NotFound, Forbidden
from pymongo import ASCENDING, DESCENDING
from copy import deepcopy

from flow.libs.databases.connection_builder import get_storage_connection
from flow.libs.databases.storage.paginator import Paginator
from flow.libs.datetime import now_utc_datetime

MAP_SORTING = {
    'ASC': ASCENDING,
    'DESC': DESCENDING
}


class CrudBase(object):
    """
    Classe base responsável por lidar com métodos de interação com o CRUD no MongoDB
    """

    subject = None
    database = None
    verify_insert = None
    key_fields = None

    def __init__(self):
        """
        Inicialização do objeto
        """

        self.__connection = None

    def clear_cache(self, old_data: dict, is_multi: bool):
        """
        Método acionado para proceder com limpeza de cache

        O mesmo deve ser implementando nas classes filha da classe StorageBase

        :param old_data: Dados antes da alteração. Se is_multi for False, esse valor será um dicionário em branco
        :param is_multi: Indica se está alterando mais do que um documento
        """
        pass

    @property
    def connection(self):
        """
        Propriedade para devolver uma connection configurada
        """
        if self.__connection is None:
            self.__connection = get_storage_connection('STORAGE', self.database, self.subject)

        return self.__connection

    @staticmethod
    def __normalize_sorting(sorting: list):
        if not sorting:
            return [("_id", ASCENDING)]

        return [
            (item.split('#')[0], MAP_SORTING.get(item.split('#')[1], ASCENDING)) for item in sorting
        ]

    def normalize_item(self, data: dict) -> dict or None:
        """
        Método para normalizar um item. A principal ideia aqui é permitir que esse método seja extendido
        em classes derivadas

        :param data: Item a ser normalizado
        :return: Item normalizado
        """

        if not data:
            return None

        if "_id" in data:
            data["_id"] = str(data["_id"])

        return data

    def normalize_item_list(self, data: dict) -> dict or None:
        """
        Método para normalizar um item de uma lista. A principal ideia aqui é permitir que esse método seja extendido
        em classes derivadas

        :param data: Item a ser normalizado
        :return: Item normalizado
        """
        if not data:
            return None

        if "_id" in data:
            data["_id"] = str(data["_id"])

        return data

    @staticmethod
    def __normalize_projection(_projection: list):
        if not _projection:
            return None

        projection = {item: 1 for item in _projection}

        if "_id" not in projection:
            projection['_id'] = 0

        return projection

    def __normalize_key(self, data: dict) -> dict:
        """
        Método para normalizar a chave de busca e validação de item

        Somente o primeiro nível so Json/Dict é considerado

        :param data: Dados específicos
        :return: Dicionário com a chave normalizada
        """

        key = {item: data.get(item) for item in self.key_fields}

        self.__extend_filter(key)

        return key

    def __extend_filter(self, _filter: dict):
        """
        Método para normalizar e extender um filtro (para verificar a existência do registro)

        A particularidade fica sobre o campo _id que se existir deve conter um ObjectID

        :param _filter: Filtro não extendido
        :return: Dicionário com o filtro extendido e normalizado
        """
        if _filter is None:
            _filter = dict()

        if '_id' in _filter and isinstance(_filter['_id'], str):
            _filter['_id'] = ObjectId(_filter['_id'])

        return _filter

    @staticmethod
    def __query_to_string(key: dict):
        """
        Método para transformar uma chave em uma string legível

        :param key: Dicionário com a chave normalizada
        :return: String legível da chave
        """

        fields = list()

        for k, v in key.items():
            fields.append(f'{k}: {str(v)}')

        return ', '.join(fields)

    def __validate_resource(self, key: dict, _id: str=None):
        """
        Validador da existência de um recurso com base nos campos chave. Apenas quando a flag verify_insert estiver
        atiada.

        :param key: Dicionário com a chave normalizada
        :param _id: Id do documento atual (usado para verificação de edição)
        """

        _filter = deepcopy(key)

        if _id:
            _filter['_id'] = {
                '$ne': ObjectId(_id)
            }

        exists = self.connection.find(_filter).limit(1).count(True) > 0

        if exists:
            raise Forbidden(f'O recurso com a chave [{self.__query_to_string(key)}] já existe')

    def insert_one(self, data: dict) -> dict:
        """
        Insere um item no Storage

        :param data: item a ser inserido
        """

        if self.verify_insert:
            key = self.__normalize_key(data)
            self.__validate_resource(key)

        data['__inserted__'] = {
            'at': now_utc_datetime()
        }

        _id = str(self.connection.insert_one(data).inserted_id)
        return {'_id': _id}

    def insert_many(self, items: list) -> dict:
        """
        Insere mais do que um item no Storage

        :param items: Lista de itens a serem inseridos
        """

        for item in items:

            if self.verify_insert:
                key = self.__normalize_key(item)
                self.__validate_resource(key)

            item['__inserted__'] = {
                'at': now_utc_datetime()
            }

        res = self.connection.insert_many(items)
        return {'_ids': [str(_id) for _id in res.inserted_ids]}

    def find_many(self, query: dict=None, projection: list=None, page_number: int=None, per_page: int=None,
             sorting: list=None) -> dict:
        """
        Obtem uma listagem dos itens

        :param query: Dicionário contendo um filtro pré informado
        :param projection: Lista contendo a projeção de dados
        :param page_number: Número da página
        :param per_page: Itens por página
        :param sorting: Lista contendo a ordenação dos dados
        """

        cursor = self.connection.find(
            self.__extend_filter(query),
            self.__normalize_projection(projection)
        ).sort(self.__normalize_sorting(sorting))

        if page_number:
            p = Paginator(cursor, per_page=per_page or 25)
            page = p.page(page_number)

            _list = [self.normalize_item(item) for item in page.object_list]

            return {
                'page_records': len(_list),
                'total_records': p.count,
                'list': _list,
                'page': page_number,
                'total_pages': p.num_pages,
                'per_page': per_page
            }
        else:
            _list = [self.normalize_item(item) for item in cursor]

            return {
                'total_records': len(_list),
                'list': _list
            }

    def find_one(self, _id: str, projection: list=None) -> dict:
        """
        Obtem um item específico
        :param _id: Identificação do Item
        :param projection: Lista contendo a projeção de dados
        """

        query = self.__extend_filter({
            "_id": ObjectId(_id)
        })

        item = self.connection.find_one(
            query,
            self.__normalize_projection(projection)
        )

        if not item:
            raise NotFound(f'Registro [{self.__query_to_string(query)}] não localizado')

        return self.normalize_item(item)

    def update_one(self, _id: str, data: dict):
        """
        Atualiza um item específico

        :param _id: Identificação do Item
        :param data: Dados da atualização do item
        """
        if self.verify_insert:
            key = self.__normalize_key(data)
            self.__validate_resource(key, _id)

        old_item = self.find_one(_id)

        query = self.__extend_filter({
            "_id": ObjectId(_id)
        })

        data['__updated__'] = {
            'at': now_utc_datetime()
        }

        res = self.connection.update_one(
            self.__extend_filter(query),
            {'$set': data}
        )

        self.clear_cache(old_item, False)

        return {'matched': res.matched_count, 'updated': res.modified_count}

    def remove_one(self, _id: str):
        """
        Deleta um item específico

        :param _id: Identificação do Item
        """
        old_item = self.find_one(_id)

        query = self.__extend_filter({
            "_id": ObjectId(_id)
        })

        res = self.connection.delete_one(
            self.__extend_filter(query)
        )

        self.clear_cache(old_item, False)

        return {'deleted': res.deleted_count}

    def remove_many(self, query: dict=None):
        """
        Deleta mais do que um item

        :param query: Dicionário contendo um filtro pré informado
        """

        query = self.__extend_filter(query)

        res = self.connection.delete_many(
            self.__extend_filter(query)
        )

        self.clear_cache({}, True)

        return {'deleted': res.deleted_count}
