"""Configuration values"""
import os


DEBUG = os.getenv('APP_DEBUG', 'true').lower() == 'true'
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv('APP_CORS_ORIGINS', '').split(',')
]
CORS_ORIGIN_REGEX = os.getenv('APP_CORS_ORIGIN_REGEX', r'https?://.*\.rex\.sh')

SESSION_ID_HEADER = os.getenv('APP_SESSION_ID_HEADER', 'x-client-id')

REXUI_CALLBACK_HOST = os.getenv('REX_REXUI_SERVER_CALLBACK_HOST')

REXFLOW_HOST = os.getenv('REX_REXFLOW_HOST')
REXFLOW_FLOWD_HOST = os.getenv('REX_REXFLOW_FLOWD_HOST')
