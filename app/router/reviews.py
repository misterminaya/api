from typing import List
from fastapi import APIRouter, HTTPException
from fastapi import Depends
from ..schemas import ReviewRequestModel, ReviewResponseModel, ReviewRequestPutModel
from ..database import User, Movie, UserReview
from ..common import get_current_user



router = APIRouter(prefix='/reviews', tags=['Reviews'])


@router.post('', response_model=ReviewResponseModel, status_code=201)
async def create_review(user_review: ReviewRequestModel,user: User = Depends(get_current_user)):
    # Verifica si la película existe
    if not Movie.select().where(Movie.id == user_review.movie_id).exists():
        raise HTTPException(status_code=404, detail="Película no encontrada.")

    # Crea el review
    created_review = UserReview.create(
        user_id=user.id,  # Usuario autenticado (dueño del review)
        movie=user_review.movie_id,
        reviews=user_review.reviews,
        score=user_review.score
    )

    return created_review


@router.get('', response_model=list[ReviewResponseModel])
async def get_reviews(page: int = 1, limit: int = 10):
    reviews = UserReview.select().paginate(page, limit)

    if not reviews:
        raise HTTPException(status_code=404, detail="No hay reseñas disponibles.")
    
    return list(reviews)


@router.get('/{review_id}', response_model=ReviewResponseModel)
async def get_review(review_id: int):
    review = UserReview.select().where(UserReview.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Reseña no encontrada.")

    return review


@router.put('/{review_id}', response_model=ReviewResponseModel)
async def update_review(review_id: int, review_request: ReviewRequestPutModel,user: User = Depends(get_current_user)):
    review = UserReview.select().where(UserReview.id == review_id).first()

    if not review:
        raise HTTPException(status_code=404, detail="Reseña no encontrada.")
    
    if review.user_id != user.id:
        raise HTTPException(status_code=403, detail="No tienes permiso para editar esta reseña.")

    review.reviews = review_request.reviews
    review.score = review_request.score
    review.save()

    return review

@router.delete('/{review_id}', response_model=ReviewResponseModel)
async def delete_review(review_id: int, user: User = Depends(get_current_user)):
    review = UserReview.select().where(UserReview.id == review_id).first()

    if review and review.user_id != user.id:
        raise HTTPException(status_code=403, detail="No tienes permiso para eliminar esta reseña.")
    
    if not review:
        raise HTTPException(status_code=404, detail="Reseña no encontrada.")
    
    review.delete_instance()
    return review
