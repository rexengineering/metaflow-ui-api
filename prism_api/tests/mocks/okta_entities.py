from prism_api.okta.entities import (
    Token,
)


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
