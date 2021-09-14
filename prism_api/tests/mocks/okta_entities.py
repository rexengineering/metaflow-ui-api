from .graphql_info import MockInfo
from prism_api.okta.entities import (
    JWKS,
    JWKSResponse,
    Token,
)
from prism_api.okta.settings import AUTHORIZATION_HEADER


def mock_info_with_token():
    info = MockInfo()
    info.context['request'].headers[AUTHORIZATION_HEADER] = 'MOCK_TOKEN'
    return info


def mock_token():
    return Token(
        ver=1,
        jti='AT.0mP4JKAZX1iACIT4vbEDF7LpvDVjxypPMf0D7uX39RE',
        iss='https://${yourOktaDomain}/oauth2/0oacqf8qaJw56czJi0g4',
        aud='https://api.example.com',
        sub='00ujmkLgagxeRrAg20g3',
        iat=1467145094,
        exp=1467148694,
        cid='nmdP1fcyvdVO11AL7ECm',
        uid='00ujmkLgagxeRrAg20g3',
        scp=[],
    )


N = '''
iKqiD4cr7FZKm6f05K4r-GQOvjRqjOeFmOho9V7SAXYwCyJluaGBLVvDWO1XlduPLOrsG_Wgs67SOG5qeLPR8T1zDK4bfJAo1Tvbw
YeTwVSfd_0mzRq8WaVc_2JtEK7J-4Z0MdVm_dJmcMHVfDziCRohSZthN__WM2NwGnbewWnla0wpEsU3QMZ05_OxvbBdQZaDUsNSx4
6is29eCdYwhkAfFd_cFRq3DixLEYUsRwmOqwABwwDjBTNvgZOomrtD8BRFWSTlwsbrNZtJMYU33wuLO9ynFkZnY6qRKVHr3YToIrq
NBXw0RWCheTouQ-snfAB6wcE2WDN3N5z760ejqQ
'''


def mock_jwks():
    return JWKS(
        alg='RS256',
        e='AQAB',
        n=N,
        kid='U5R8cHbGw445Qbq8zVO1PcCpXL8yG6IcovVa3laCoxM',
        kty='RSA',
        use='sig',
    )


def mock_jwks_response():
    return JWKSResponse(
        keys=[mock_jwks()],
    )
