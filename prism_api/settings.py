"""Configuration values"""
import os


DEBUG = os.getenv('APP_DEBUG', 'true').lower() == 'true'
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv('APP_CORS_ORIGINS', '').split(',')
]
CORS_ORIGIN_REGEX = os.getenv('APP_CORS_ORIGIN_REGEX', r'https?://.*\.rex\.sh')
BRIDGE_RATE_LIMIT_SECONDS = float(os.getenv('APP_BRIDGE_RATE_LIMIT_SECONDS', 0))  # noqa #501
DISABLE_AUTHENTICATION = os.getenv('APP_DISABLE_AUTHENTICATION', 'false').lower() == 'true'  # noqa E501

REXUI_CALLBACK_HOST = os.getenv('REX_REXUI_SERVER_CALLBACK_HOST')

REXFLOW_HOST = os.getenv('REX_REXFLOW_HOST')
REXFLOW_FLOWD_HOST = os.getenv('REX_REXFLOW_FLOWD_HOST')


TALKTRACK_WORKFLOWS = list([s.strip() for s in os.getenv('APP_TALKTRACK_WORKFLOWS', '').split(',')])  # noqa E501
