from app.auth import create_access_token, decode_access_token


def test_token_roundtrip():
    token = create_access_token('alice')
    assert decode_access_token(token) == 'alice'
