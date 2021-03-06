"""Configuration values"""
import os

from rexflow_ui import settings as rexflow_settings

DEBUG = os.getenv('APP_DEBUG', 'true').lower() == 'true'
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

RUN_INTEGRATION_TESTS = os.getenv('INTEGRATION_TESTS', False)
INTEGRATION_TEST_HOST = os.getenv('APP_INTEGRATION_TEST_HOST')

CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv('APP_CORS_ORIGINS', '').split(',')
]
CORS_ORIGIN_REGEX = os.getenv('APP_CORS_ORIGIN_REGEX', r'https?://.*\.rex\.sh')
DISABLE_AUTHENTICATION = os.getenv('APP_DISABLE_AUTHENTICATION', 'false').lower() == 'true'  # noqa E501

APP_HOST = os.getenv('PRISM_API_SERVICE_HOST')
if APP_HOST and rexflow_settings.REXUI_CALLBACK_HOST is None:
    rexflow_settings.REXUI_CALLBACK_HOST = f'http://{APP_HOST}/callback/'

TALKTRACK_WORKFLOWS = list([s.strip() for s in os.getenv('APP_TALKTRACK_WORKFLOWS', '').split(',')])  # noqa E501
