from ariadne.exceptions import HttpError


class HttpUnauthorizedError(HttpError):
    status = '401 Unauthorized'
