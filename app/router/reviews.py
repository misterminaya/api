from typing import List
from fastapi import APIRouter, HTTPException
from fastapi import Depends
from sqlalchemy.orm import Session
from ..schemas import ReviewRequestModel, ReviewResponseModel, ReviewRequestPutModel
from ..database import User, Movie, UserReview, get_db
from ..common import get_current_user



router = APIRouter(prefix='/reviews', tags=['Reviews'])


@router.post('', response_model=ReviewResponseModel, status_code=201)
async def create_review(
    user_review: ReviewRequestModel,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not db.query(Movie).filter(Movie.id == user_review.movie_id).first():
        raise HTTPException(status_code=404, detail="Película no encontrada.")

    created_review = UserReview(
        user_id=user.id,
        movie_id=user_review.movie_id,
        reviews=user_review.reviews,
        score=user_review.score,
    )
    db.add(created_review)
    db.commit()
    db.refresh(created_review)
    return created_review


@router.get('', response_model=list[ReviewResponseModel])
async def get_reviews(page: int = 1, limit: int = 10, db: Session = Depends(get_db)):
    reviews = db.query(UserReview).offset((page - 1) * limit).limit(limit).all()

    if not reviews:
        raise HTTPException(status_code=404, detail="No hay reseñas disponibles.")

    return reviews


@router.get('/{review_id}', response_model=ReviewResponseModel)
async def get_review(review_id: int, db: Session = Depends(get_db)):
    review = db.query(UserReview).filter(UserReview.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Reseña no encontrada.")

    return review


@router.put('/{review_id}', response_model=ReviewResponseModel)
async def update_review(
    review_id: int,
    review_request: ReviewRequestPutModel,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    review = db.query(UserReview).filter(UserReview.id == review_id).first()

    if not review:
        raise HTTPException(status_code=404, detail="Reseña no encontrada.")
    
    if review.user_id != user.id:
        raise HTTPException(status_code=403, detail="No tienes permiso para editar esta reseña.")

    review.reviews = review_request.reviews
    review.score = review_request.score
    db.commit()
    db.refresh(review)

    return review

@router.delete('/{review_id}', response_model=ReviewResponseModel)
async def delete_review(
    review_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    review = db.query(UserReview).filter(UserReview.id == review_id).first()

    if review and review.user_id != user.id:
        raise HTTPException(status_code=403, detail="No tienes permiso para eliminar esta reseña.")
    
    if not review:
        raise HTTPException(status_code=404, detail="Reseña no encontrada.")
    
    db.delete(review)
    db.commit()
    return review
