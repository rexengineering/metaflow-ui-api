"""Configuration values"""
import os


DEBUG = os.getenv('APP_DEBUG', 'true').lower() == 'true'
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv('APP_CORS_ORIGINS', '').split(',')
]
CORS_ORIGIN_REGEX = os.getenv('APP_CORS_ORIGIN_REGEX', 'https?://.*\.rex\.sh')

REXFLOW_HOST = os.getenv('REX_REXFLOW_HOST')
REXFLOW_HOST_INSTANCE = os.getenv('REX_REXFLOW_HOST_INSTANCE')
