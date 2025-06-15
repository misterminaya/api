from typing import List

from fastapi import FastAPI
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from fastapi.routing import APIRouter as ApiRouter
from fastapi.security import OAuth2PasswordRequestForm


from .database import User
from .database import Movie
from .database import UserReview

from .router import users_router
from .router import reviews_router
from .common import create_access_token

import time
from .database import database as connection
import logging
from peewee import OperationalError



logging.basicConfig(level=logging.INFO)

app = FastAPI(title='Proyecto para reseñar peliculas',
              description='En este proyecto seremos capaces de reseñar peliculas',
              version='1.0.0')


api_v1 = ApiRouter(prefix='/api/v1', tags=['API v1'])


api_v1.include_router(users_router)
api_v1.include_router(reviews_router)

@api_v1.post('/auth')
async def authenticate_user(data: OAuth2PasswordRequestForm = Depends()):
    user = User.authenticate(username=data.username, password=data.password)

    if user:
        return {
            'access_token': create_access_token(user),
            'token_type': 'bearer'
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    

app.include_router(api_v1)

@app.on_event('startup')
def startup():
    for i in range(10):  # hasta 10 intentos
        try:
            if connection.is_closed():
                connection.connect()
            connection.create_tables([User, Movie, UserReview])
            logging.info("✅ Conectado a MySQL y tablas listas.")
            break
        except OperationalError as e:
            logging.warning(f"❌ Intento {i+1}: No se pudo conectar a MySQL. Esperando 3s...")
            time.sleep(3)
    else:
        logging.error("❌ Falló la conexión a MySQL después de varios intentos.")
        raise Exception("No se pudo conectar a la base de datos.")


@app.on_event('shutdown')
def shutdown():
    if not connection.is_closed():
        connection.close()

    logging.info('El servidor se encuentra finalizando.')





