from typing import List

from pydantic import BaseModel


class TokenWrapper(BaseModel):
    access_token: str
    token_type: str


class TokenHeader(BaseModel):
    alg: str  # encryption algorithm
    kid: str  # public key identifier


class Token(BaseModel):
    ver: int  # token version
    jti: str  # identifier for debugging and revocation
    iss: str  # response issue identifier
    aud: str  # audience
    sub: str  # subject
    iat: int  # issue time
    exp: int  # expiration time
    cid: str  # client id
    uid: str  # user unique identifier
    scp: List[str]  # granted scopes


class JWKS(BaseModel):
    alg: str  # encryption algorithm
    e: str  # RSA key value for key blinding
    n: str  # RSA modulus
    kid: str  # Key id
    kty: str  # algorithm family
    use: str  # How the key is used


class JWKSResponse(BaseModel):
    keys: List[JWKS]
