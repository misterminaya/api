from typing import Any
from pydantic import BaseModel, EmailStr
from pydantic import validator

from peewee import ModelSelect

from pydantic.utils import GetterDict


class PeeweeGetterDict(GetterDict):
    def get(self, key:Any, default: Any = None):
        
        res = getattr(self._obj, key, default)
        if isinstance(res, ModelSelect):
            return list(res)
        return res

class ResponseModel(BaseModel):
    class Config:
        orm_mode = True
        getter_dict = PeeweeGetterDict

#------------------------ User ------------------------

class UserRequestModel(BaseModel):
    username: str
    email: EmailStr
    password: str

    @validator('username')
    def username_validator(cls, username):
        if len(username) < 3:
            raise ValueError('El nombre de usuario debe tener al menos 3 caracteres.')
        return username

    @validator('password')
    def password_validator(cls, password):
        if len(password) < 6:
            raise ValueError('La contrasena debe tener al menos 6 caracteres.')
        return password


class UserResponseModel(ResponseModel):
    id: int
    username: str
    email: str
    is_verified: bool


class OTPVerifyRequestModel(BaseModel):
    email: EmailStr
    code: str

    @validator('code')
    def code_validator(cls, code):
        if len(code) != 6 or not code.isdigit():
            raise ValueError('El codigo OTP debe ser de 6 digitos.')
        return code


class ResendOTPRequestModel(BaseModel):
    email: EmailStr


class MessageResponseModel(BaseModel):
    message: str

#------------------------ Movie ------------------------

class MovieResponseModel(ResponseModel):
    id: int
    title: str

#------------------------ Review ------------------------

class ReviewValidator():
    reviews: str
    score: int

    @validator('score')
    def score_validator(cls, score):
        if score < 1 or score > 5:
            raise ValueError('La puntuación debe estar entre 1 y 5.')
        return score

class ReviewRequestModel(BaseModel, ReviewValidator):
    movie_id:int
    reviews: str
    score: int
    
class ReviewResponseModel(ResponseModel):
    id:int
    movie: MovieResponseModel
    reviews: str
    score: int

class ReviewRequestPutModel(BaseModel, ReviewValidator):
    reviews: str
    score: int

