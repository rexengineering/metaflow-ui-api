import os


BASE_URI = os.getenv('OKTA_BASE_URI')
CLIENT_ID = os.getenv('OKTA_CLIENT_ID')
CLIENT_SECRET = os.getenv('OKTA_CLIENT_SECRET')
ISSUER_URL = os.getenv('OKTA_ISSUER_URL')
AUDIENCE = os.getenv('OKTA_AUDIENCE')

ID_TOKEN_HEADER = os.getenv('APP_ID_TOKEN_HEADER', 'x-id-token')
AUTHORIZATION_HEADER = os.getenv('APP_AUTHORIZATION_HEADER', 'authorization')
