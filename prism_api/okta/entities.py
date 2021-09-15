from typing import List, Optional

from pydantic import BaseModel, Json


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


class IdToken(BaseModel):
    ver: int  # token version
    sub: str  # subjet
    iss: str  # url of the issuer autorization server
    aud: str  # audience
    iat: int  # issue time
    exp: int  # expiration time
    amr: List[str]  # array of authentication methods identifiers
    jti: str  # identifier for debugging and revocation
    auth_time: int  # time the end user was authenticated
    at_hash: Optional[str]  # access token hash value

    # scope dependend values
    name: Optional[str]
    nickname: Optional[str]
    preferred_username: Optional[str]
    given_name: Optional[str]
    middle_name: Optional[str]
    family_name: Optional[str]
    profile: Optional[str]
    zoneinfo: Optional[str]
    locale: Optional[str]
    updated_at: Optional[int]  # time the user information was last updated
    email: Optional[str]
    email_verified: Optional[bool]
    address: Optional[Json]
    phone_number: Optional[str]
    groups: Optional[List[str]]


class JWKS(BaseModel):
    alg: str  # encryption algorithm
    e: str  # RSA key value for key blinding
    n: str  # RSA modulus
    kid: str  # Key id
    kty: str  # algorithm family
    use: str  # How the key is used


class JWKSResponse(BaseModel):
    keys: List[JWKS]
