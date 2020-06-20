from flow.libs.databases.connection_builder import get_in_memory_connection


class State:
    __slots__ = ('type', 'subject', '__separator', '__ttl', '__server')

    def __init__(self, separator=':'):
        self.__separator = separator
        self.__ttl = 0
        self.__server = None
        self.type = 'STATE'
        self.subject = 'NA'

    def __str__(self):
        properties = list()
        classes = list(type(self).__mro__)
        classes.reverse()

        for item in classes:
            if issubclass(item, State):
                properties.extend(item.__slots__)

        return self.__separator.join(str(getattr(self, key)) for key in properties if not key.startswith('__'))

    @property
    def ttl(self):
        return self.__ttl

    @ttl.setter
    def ttl(self, value):
        self.__ttl = value

    def exists(self) -> bool:
        return self.connection.exists(str(self))

    def delete(self):
        keys = self.connection.keys(str(self))
        for item in keys:
            self.connection.delete(item.decode())

    def reset_value(self):
        if self.exists():
            self.delete()

    @staticmethod
    def _buffer_decode(buffer: dict):
        return {k.decode(): v.decode() for k, v in buffer.items()}

    @property
    def connection(self):
        if self.__server is None:
            self.__server = get_in_memory_connection('STATE')

        return self.__server

    def get_value(self) -> dict:
        buffer = self.connection.hgetall(str(self))
        if buffer:
            return self._buffer_decode(buffer)

    def get_field(self, field_name: str):
        """Recupera o valor de um campo interno do HASH"""
        buffer = self.connection.hget(str(self), field_name)
        return buffer.decode() if buffer else None

    def get_fields(self, field_names: list):
        values = self.connection.hmget(str(self), field_names)
        return dict(zip(field_names, [item.decode() if item is not None else None for item in values]))

    def set_value(self, data: dict):
        self.reset_value()
        pipe = self.connection.pipeline()
        pipe.hmset(str(self), data)
        if self.ttl:
            pipe.expire(str(self), self.ttl)
        pipe.execute()

    def set_field(self, field_name: str, field_value: str):
        pipe = self.connection.pipeline()
        pipe.hset(str(self), field_name, field_value)
        if self.ttl:
            pipe.expire(str(self), self.ttl)
        pipe.execute()

    def set_fields(self, data: dict):
        pipe = self.connection.pipeline()
        pipe.hmset(str(self), data)
        if self.ttl:
            pipe.expire(str(self), self.ttl)
        pipe.execute()
