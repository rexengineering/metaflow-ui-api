"""Check the system dependency on other services"""


def _check_redis_service():
    return True


services = {
    'redis': _check_redis_service,
}


def check_status():
    results = {}
    for name, status in services.items():
        results[name] = status()

    return results
