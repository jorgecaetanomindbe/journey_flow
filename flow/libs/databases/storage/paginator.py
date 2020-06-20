# coding: utf-8

import collections
import pymongo.cursor
from math import ceil

from werkzeug.exceptions import BadRequest


class Paginator(object):
    """
    - :param object_list: Uma lista, tupla, QuerySet, ou outro objeto contável por
    um método count() ou __len__()

    - :param per_page: O número máximo de ítens que serão incluídos na página, não
    incluíndo orfãos (veja o argumento opcional orphans abaixo).

    - :param orphans: O número mínimo de ítens permitidos em uma última página, o
    padrão é zero. Use isto quando você não quiser ter uma última página com
    pouquíssimos ítens. Se a última página poderá ter um número de ítens menor que
    ou igual ao orphans, então estes ítens serão adicionados na página anterior (que
    se torna a última página) ao invés de deixados em uma página só para eles. Por
    exemplo, com 23 ítens, per_pager=10, e orphans=3, haverá duas páginas; a primeira
    com 10 ítens e a segunda (e última) com 13 items.

    - :param allow_empty_first_page: Permite ou não a primeira página ser vazia. Se
    for `False` e object_list estiver vazio, então um erro EmtpyPage será levantado.
    """
    def __init__(self, object_list, per_page, orphans=0,
                 allow_empty_first_page=True):
        self.object_list = object_list
        self.per_page = int(per_page)
        self.orphans = int(orphans)
        self.allow_empty_first_page = allow_empty_first_page
        self._num_pages = self._count = None

    def validate_number(self, number):
        """Válida se o valor é baseado em número de página.
        :param number:
            Inteiro que representa o número da página desejada.
        """
        try:
            number = int(number)
        except (TypeError, ValueError):
            raise BadRequest('O número da página precisa ser um número inteiro')
        if number < 1:
            raise BadRequest('O número da página precisa ser maior que 0')
        if number > self.num_pages and not (number == 1 and self.allow_empty_first_page):
            raise BadRequest('A página solicitada não contém regitros')
        return number

    def page(self, number):
        """ Retorna um objeto :class:`Page` com um determinado índice. Se a determinada
        página não existe, é lançado uma exceção :exception:`InvalidPage`.

        :param number:
            Inteiro que representa o número da página desejada.
        """
        number = self.validate_number(number)
        bottom = (number - 1) * self.per_page
        top = bottom + self.per_page
        if top + self.orphans >= self.count:
            top = self.count
        if isinstance(self.object_list, pymongo.cursor.Cursor):
            self.object_list = self.object_list.clone()
        return self._get_page(self.object_list[bottom:top], number, self)

    def _get_page(self, *args, **kwargs):
        """
        - :param: number: inteiro
        - :param: object_list: self.object_list
        - :param: paginator: self
        """
        return Page(*args, **kwargs)

    def _get_count(self):
        """O número total de objetos, através de todas as páginas.
        """
        if self._count is None:
            try:
                if isinstance(self.object_list, pymongo.cursor.Cursor):
                    self._count = self.object_list.count(with_limit_and_skip=True)
                else:
                    self._count = self.object_list.count()
            except (AttributeError, TypeError):
                self._count = len(self.object_list)
        return self._count
    count = property(_get_count)

    def _get_num_pages(self):
        """O número total de páginas."""
        if self._num_pages is None:
            if self.count == 0 and not self.allow_empty_first_page:
                self._num_pages = 0
            else:
                hits = max(1, self.count - self.orphans)
                self._num_pages = int(ceil(hits / float(self.per_page)))
        return self._num_pages

    num_pages = property(_get_num_pages)

    def _get_page_range(self):
        """Um número começando com 1 de páginas, por exemplo, [1, 2, 3, 4].
        """
        return list(range(1, self.num_pages + 1))
    page_range = property(_get_page_range)


class Page(collections.Sequence):
    """
    - :param: number: O número desta página.
    - :param: object_list: A lista de objetos nesta página.
    - :param: paginator: :class:`paginator.Paginator`
    """
    def __init__(self, object_list, number, paginator):
        self.object_list = object_list
        self.number = number
        self.paginator = paginator

    def __repr__(self):
        return '<Page %s of %s>' % (self.number, self.paginator.num_pages)

    def __len__(self):
        raise NotImplementedError

    def __getitem__(self, index):
        if not isinstance(index, (slice, int)):
            raise TypeError
        if not isinstance(self.object_list, list):
            self.object_list = list(self.object_list)
        return self.object_list[index]

    def has_next(self):
        """Retorna `True` se existe uma página subseqüente."""
        return self.number < self.paginator.num_pages

    def has_previous(self):
        """Retorna `True` se existe uma página anterior."""
        return self.number > 1

    def has_other_pages(self):
        """Retorna `True` se existe uma página subseqüente ou anterior."""
        return self.has_previous() or self.has_next()

    def next_page_number(self):
        """Retorna o número da página subseqüente. Note que este é um método "burro" e
        vai apenas retornar o número da página subseqüente, a página existindo ou não."""
        return self.paginator.validate_number(self.number + 1)

    def previous_page_number(self):
        """Retorna o número da página anterior. Note que este é um método "burro" e vai
        apenas retornar o número da página anterior, a página existindo ou não."""
        return self.paginator.validate_number(self.number - 1)

    def start_index(self):
        """Retorna o índice iniciado em 1 do primeiro objeto na página, relativo a todos
        os objetos na lista do paginador. Por exemplo, quando se pagina uma lista com 5
        objetos a 2 objetos por página, o start_index() da segunda página devolveria 3."""
        # Special case, return zero if no items.
        if self.paginator.count == 0:
            return 0
        return (self.paginator.per_page * (self.number - 1)) + 1

    def end_index(self):
        """Retorna o índice iniciado em 1 do último objeto na página, relativo a todos os
        objetos na lista do paginador. Por exemplo, quando se pagina uma lista com 5 objetos
        a 2 objetos por página, o end_index() da segunda página devolveria 4."""
        # Special case for the last page because there can be orphans.
        if self.number == self.paginator.num_pages:
            return self.paginator.count
        return self.number * self.paginator.per_page
