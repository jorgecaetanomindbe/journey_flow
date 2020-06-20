from datetime import datetime
from pytz import timezone, utc


def datetime_from_utc(utctime: datetime, str_zone: str = 'America/Sao_Paulo') -> datetime:
    """
    Converte um horário UTC para a zona de horário informada

    :param utctime:
        Horário em UTC
    :param str_zone:
        Fuso horário de destino
    :return:
        Horário localizado para o fuso horário informado
    """
    zone = timezone(str_zone)

    if utctime.tzinfo == utc:
        buffer = utctime.astimezone(zone)
    else:
        buffer = zone.fromutc(utctime)

    return buffer


def now_utc_datetime() -> datetime:
    """
    Retorna a data e hora em UTC

    :return:
        Datetime no fuso UTC
    """

    return datetime.utcnow().replace(tzinfo=utc)


def datetime_to_utc(localtime: datetime, zone: str = 'America/Sao_Paulo') -> datetime:
    """
    Converte a hora local, de acordo com a zona de horário, para UTC

    :param localtime:
        Horário local
    :param zone:
        Fuso horário de origem
    :return:
        Datetime no fuso UTC
    """
    fuso = timezone(zone)

    ano, mes, dia, hora, minuto, segundo, *_ = localtime.timetuple()
    lc = fuso.localize(datetime(ano, mes, dia, hora, minuto, segundo))
    return lc.astimezone(utc)

