from flow.libs.databases.connection_builder import get_in_memory_connection
from json import dumps, loads


class Cache:
    __slots__ = ('type', 'subject', '__separator', '__ttl', '__server')

    def __init__(self, separator=':', subject='NA'):
        self.__separator = separator
        self.__server = None
        self.__ttl = 0
        self.type = 'CACHE'
        self.subject = subject

    @property
    def ttl(self):
        return self.__ttl

    @ttl.setter
    def ttl(self, value):
        self.__ttl = value

    def __str__(self):
        properties = list()
        classes = list(type(self).__mro__)
        classes.reverse()

        for item in classes:
            if issubclass(item, Cache):
                properties.extend(item.__slots__)

        return self.__separator.join(str(getattr(self, key)) for key in properties if not key.startswith('__'))

    @property
    def connection(self):
        if self.__server is None:
            self.__server = get_in_memory_connection('CACHE')

        return self.__server

    def get_value(self) -> dict:
        buffer = self.connection.get(str(self))
        if buffer:
            return loads(buffer.decode())

    def set_value(self, buffer: dict):
        if self.ttl:
            self.connection.setex(str(self), self.ttl, dumps(buffer))
        else:
            self.connection.set(str(self), dumps(buffer))

    def delete(self):
        keys = self.connection.keys(str(self))
        for item in keys:
            self.connection.delete(item.decode())
