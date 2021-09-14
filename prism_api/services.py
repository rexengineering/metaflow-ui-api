"""Check the system dependency on other services"""
import httpx

from rexredis import RexRedis

from prism_api import settings


def _check_redis_service():  # pragma: no cover
    redis = RexRedis()
    return redis.ping()


def _check_rexflow_service():  # pragma: no cover
    if not settings.REXFLOW_FLOWD_HOST:
        return 'Not Configured'

    try:
        res = httpx.get(settings.REXFLOW_FLOWD_HOST + '/health')
        return res.status_code == 200
    except httpx.ConnectError:
        return False


services = {
    'redis': _check_redis_service,
    'rexflow-bridge': _check_rexflow_service,
}


def check_status():  # pragma: no cover
    results = {}
    for name, status in services.items():
        results[name] = status()

    return results
