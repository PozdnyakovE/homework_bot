class BadRequestError(Exception):
    """Вызывается при ошибках выполнения запросов к API."""

    pass


class NotJSONError(Exception):
    """Вызывается при ошибках преобразования к типу данных Python."""

    pass
