from typing import List
from typing import Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi import Response
from fastapi import Cookie
from fastapi import Depends

from fastapi.security import HTTPBasicCredentials
from ..database import User, OTPCode
from ..schemas import UserRequestModel, UserResponseModel
from ..schemas import ReviewResponseModel
from ..schemas import OTPVerifyRequestModel, ResendOTPRequestModel, MessageResponseModel
from ..common import get_current_user
from ..email import send_otp_email, send_welcome_email, resend_otp_email


router = APIRouter(prefix='/users', tags=['Users'])


@router.post('', response_model=MessageResponseModel, status_code=201)
async def create_user(user: UserRequestModel, background_tasks: BackgroundTasks):
    """Register a new user and send OTP verification email"""

    if User.select().where(User.username == user.username).exists():
        raise HTTPException(status_code=400, detail="El nombre de usuario ya existe.")

    if User.select().where(User.email == user.email).exists():
        raise HTTPException(status_code=400, detail="El correo electronico ya esta registrado.")

    hashed_password = User.create_password(user.password)

    # Create the user in the database (unverified)
    new_user = User.create(
        username=user.username,
        email=user.email,
        password=hashed_password,
        is_verified=False
    )

    # Generate OTP code
    otp = OTPCode.create_otp(new_user)

    # Send OTP email in background
    background_tasks.add_task(send_otp_email, user.email, user.username, otp.code)

    return {"message": "Usuario registrado. Se ha enviado un codigo de verificacion a tu correo electronico."}


@router.post('/verify-otp', response_model=UserResponseModel, status_code=200)
async def verify_otp(data: OTPVerifyRequestModel, background_tasks: BackgroundTasks):
    """Verify OTP code and activate user account"""

    user = User.select().where(User.email == data.email).first()

    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    if user.is_verified:
        raise HTTPException(status_code=400, detail="El usuario ya esta verificado.")

    # Verify OTP
    if not OTPCode.verify_otp(user, data.code):
        raise HTTPException(status_code=400, detail="Codigo OTP invalido o expirado.")

    # Mark user as verified
    user.is_verified = True
    user.save()

    # Send welcome email in background
    background_tasks.add_task(send_welcome_email, user.email, user.username)

    return user


@router.post('/resend-otp', response_model=MessageResponseModel, status_code=200)
async def resend_otp(data: ResendOTPRequestModel, background_tasks: BackgroundTasks):
    """Resend OTP verification code"""

    user = User.select().where(User.email == data.email).first()

    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    if user.is_verified:
        raise HTTPException(status_code=400, detail="El usuario ya esta verificado.")

    # Generate new OTP code
    otp = OTPCode.create_otp(user)

    # Send OTP email in background
    background_tasks.add_task(resend_otp_email, user.email, user.username, otp.code)

    return {"message": "Se ha enviado un nuevo codigo de verificacion a tu correo electronico."}


@router.post('/login', response_model=UserResponseModel, status_code=200)
async def login_user(credentials: HTTPBasicCredentials, response: Response):
    user = User.select().where(User.username == credentials.username).first()

    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Debes verificar tu cuenta antes de iniciar sesion.")

    hashed_password = User.create_password(credentials.password)

    if user.password != hashed_password:
        raise HTTPException(status_code=401, detail="Contrasena incorrecta.")

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



