from typing import List
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi import Response
from fastapi import Cookie
from fastapi import Depends

from fastapi.security import HTTPBasicCredentials
from ..database import User
from ..schemas import UserRequestModel, UserResponseModel
from ..schemas import ReviewResponseModel
from ..common import get_current_user


router = APIRouter(prefix='/users', tags=['Users'])


@router.post('', response_model=UserResponseModel, status_code=201)
async def create_user(user: UserRequestModel):

    if User.select().where(User.username == user.username).exists():
        raise HTTPException(status_code=400, detail="El nombre de usuario ya existe.")

    hashed_password = User.create_password(user.password)
    user.password = hashed_password
    # Create the user in the database       

    user = User.create(username=user.username, password=user.password) 
    return user


@router.post('/login', response_model=UserResponseModel, status_code=200)
async def login_user(credentials: HTTPBasicCredentials, response: Response):
    user = User.select().where(User.username == credentials.username).first()

    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    hashed_password = User.create_password(credentials.password)

    if user.password != hashed_password:
        raise HTTPException(status_code=401, detail="Contraseña incorrecta.")

    response.set_cookie(key="user_id", value=str(user.id), httponly=True)
    return user


"""
@router.get('/reviews', response_model=list[ReviewResponseModel])
async def get_user_reviews(user_id: int, user_id_cookie: int = Cookie(None)):
    if user_id_cookie is None or user_id_cookie != user_id:
        raise HTTPException(status_code=403, detail="No tienes permiso para ver las reseñas de este usuario.")

    user = User.select().where(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    return list(user.reviews)
"""

@router.get('/reviews', response_model=list[ReviewResponseModel])
async def get_user_reviews(user: User = Depends(get_current_user)):
   return list(user.reviews)



