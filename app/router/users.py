from typing import List
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi import Response
from fastapi import Cookie
from fastapi import Depends
from sqlalchemy.orm import Session

from fastapi.security import HTTPBasicCredentials
from ..database import User, get_db
from ..schemas import UserRequestModel, UserResponseModel
from ..schemas import ReviewResponseModel
from ..common import get_current_user


router = APIRouter(prefix='/users', tags=['Users'])


@router.post('', response_model=UserResponseModel, status_code=201)
async def create_user(user: UserRequestModel, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="El nombre de usuario ya existe.")

    hashed_password = User.create_password(user.password)
    db_user = User(username=user.username, password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.post('/login', response_model=UserResponseModel, status_code=200)
async def login_user(credentials: HTTPBasicCredentials, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == credentials.username).first()

    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    hashed_password = User.create_password(credentials.password)

    if user.password != hashed_password:
        raise HTTPException(status_code=401, detail="Contraseña incorrecta.")

    response.set_cookie(key="user_id", value=str(user.id), httponly=True)
    return user



@router.get('/reviews', response_model=list[ReviewResponseModel])
async def get_user_reviews(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
   db_user = db.query(User).filter(User.id == user.id).first()
   if not db_user:
       raise HTTPException(status_code=404, detail="Usuario no encontrado.")
   return db_user.reviews



