import jwt

from datetime import datetime, timedelta, timezone
from fastapi  import HTTPException, status
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from .database import User

SECRET_KEY = 'CodigoFacilito2021'

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth")

def create_access_token(user, days=2):
    data = {
        "user_id": user.id,
        "username": user.username,
        "exp": datetime.now(timezone.utc) + timedelta(days=days)
    }

    return jwt.encode(data, SECRET_KEY, algorithm="HS256")


def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token ha expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    payload = decode_access_token(token)
    user_id = payload.get("user_id")
    username = payload.get("username")

    if not user_id or not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return User(id=user_id, username=username)