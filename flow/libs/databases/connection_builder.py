from pymongo.collection import Collection
from pymongo.mongo_client import MongoClient
from redis import Redis
import os


def get_storage_connection(type_connection: str, database: str, subject: str) -> Collection:
    host = os.environ.get(f'STORAGE_{type_connection}_HOST', '192.168.0.14')
    port = int(os.environ.get(f'STORAGE_{type_connection}_PORT', '27017'))
    username = os.environ.get(f'STORAGE_{type_connection}_USER')

    connection = {
        'host': host,
        'port': port
    }

    if username:
        # IMPORTANTE: Caso o usuário seja 'root' o authSource será 'admin' (indicando que tem acesso a todas as bases)
        password = os.environ.get(f'STORAGE_{type_connection}_PASS')
        auth_mechanism = os.environ.get(f'STORAGE_{type_connection}_AUTH_MECHANISM', 'SCRAM-SHA-1')
        connection.update(**{
            'username': username,
            'password': password,
            'authSource': database if username != 'root' else 'admin',
            'authMechanism': auth_mechanism
        })

    return MongoClient(**connection)[database][subject]


def get_in_memory_connection(type_connection: str) -> Redis:
    host = os.environ.get(f'IN_MEMORY_{type_connection}_HOST', '192.168.0.14')
    port = os.environ.get(f'IN_MEMORY_{type_connection}_PORT', '6379')
    return Redis(host, int(port))
