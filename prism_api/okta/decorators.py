from functools import wraps


def requires_token(f):
    @wraps(f)
    def _requires_token(*args, **kwargs):
        return f(*args, **kwargs)
    return _requires_token
