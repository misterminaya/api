from typing import List

from fastapi import FastAPI
from fastapi import HTTPException

from .database import User
from .database import Movie
from .database import UserReview

import time
from .database import database as connection
import logging
from peewee import OperationalError

from .schemas import UserRequestModel
from .schemas import UserResponseModel
from .schemas import ReviewRequestModel
from .schemas import ReviewResponseModel
from .schemas import ReviewRequestPutModel


logging.basicConfig(level=logging.INFO)

app = FastAPI(title='Proyecto para reseñar peliculas',
              description='En este proyecto seremos capaces de reseñar peliculas',
              version='1.0.0')

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

@app.get("/")
async def index():
    return {"Hello": "World"}


@app.post('/users', response_model=UserResponseModel, status_code=201)
async def create_user(user: UserRequestModel):

    if User.select().where(User.username == user.username).exists():
        raise HTTPException(status_code=400, detail="El nombre de usuario ya existe.")

    hashed_password = User.create_password(user.password)
    user.password = hashed_password
    # Create the user in the database       

    user = User.create(username=user.username, password=user.password) 
    return user


@app.post('/reviesws', response_model=ReviewResponseModel,status_code=201)
async def create_review(user_review: ReviewRequestModel):
    
    if not User.select().where(User.id == user_review.user_id).exists():
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    
    if User.select().where(User.id == user_review.user_id).first() is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    

    if not Movie.select().where(Movie.id == user_review.movie_id).exists():
        raise HTTPException(status_code=404, detail="Película no encontrada.")

    user_review = UserReview.create(
        user=user_review.user_id,
        movie=user_review.movie_id,
        reviews=user_review.reviews,
        score=user_review.score
    )

    return user_review


@app.get('/reviews', response_model=list[ReviewResponseModel])
async def get_reviews(page: int = 1, limit: int = 10):
    reviews = UserReview.select().paginate(page, limit)

    if not reviews:
        raise HTTPException(status_code=404, detail="No hay reseñas disponibles.")
    
    return list(reviews)


@app.get('/reviews/{review_id}', response_model=ReviewResponseModel)
async def get_review(review_id: int):
    review = UserReview.select().where(UserReview.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Reseña no encontrada.")
    
    return review


@app.put('/reviews/{review_id}', response_model=ReviewResponseModel)
async def update_review(review_id: int, review_request: ReviewRequestPutModel):
    review = UserReview.select().where(UserReview.id == review_id).first()

    if not review:
        raise HTTPException(status_code=404, detail="Reseña no encontrada.")
    
    review.reviews = review_request.reviews
    review.score = review_request.score
    review.save()

    return review

@app.delete('/reviews/{review_id}', response_model=ReviewResponseModel)
async def delete_review(review_id: int):
    review = UserReview.select().where(UserReview.id == review_id).first()

    if not review:
        raise HTTPException(status_code=404, detail="Reseña no encontrada.")
    
    review.delete_instance()
    return review


