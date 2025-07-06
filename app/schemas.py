from typing import Any
from pydantic import BaseModel
from pydantic import validator

class ResponseModel(BaseModel):
    class Config:
        orm_mode = True

#------------------------ User ------------------------

class UserRequestModel(BaseModel):
    username: str
    password: str

    @validator('username')
    def username_validator(cls, username):
        if len(username) < 3:
            raise ValueError('El nombre de usuario debe tener al menos 3 caracteres.')
        return username


class UserResponseModel(ResponseModel):
    id: int
    username: str

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

