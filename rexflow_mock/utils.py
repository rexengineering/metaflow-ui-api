import datetime
import hashlib


def generate_xid():
    return hashlib.sha256(str(datetime.datetime.now()).encode()).hexdigest()[:16]  # noqa: E501
