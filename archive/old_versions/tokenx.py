# Python com PyJWT
import jwt
import datetime

payload = {
    'user_id': 123,
    'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
}

secret_key = 'sua_chave_secreta'
token = jwt.encode(payload, secret_key, algorithm='HS256')