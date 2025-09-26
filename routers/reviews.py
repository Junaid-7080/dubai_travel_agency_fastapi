# ===== routers/reviews.py =====
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, func
from models import Review, ReviewCreate, ReviewResponse, Booking, Package, User, BookingStatus
from schemas import APIResponse
from database import get_session
from auth import get_current_user
from datetime import datetime

router = APIRouter(prefix="/reviews", tags=["Reviews"])

@router.post("/", response_model=APIResponse)
async def create_review(
    review_data: ReviewCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Create a review for a package"""
    # Check if package exists
    package_statement = select(Package).where(Package.id == review_data.package_id)
    package = session.exec(package_statement).first()
    
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Package not found"
        )
    
    # Check if user already reviewed this package
    existing_review = session.exec(
        select(Review).where(
            Review.user_id == current_user.id,
            Review.package_id == review_data.package_id
        )
    ).first()
    
    if existing_review:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already reviewed this package"
        )
    
    # Check if user has a completed booking for this package (for verified reviews)
    is_verified = False
    if review_data.booking_id:
        booking_statement = select(Booking).where(
            Booking.id == review_data.booking_id,
            Booking.user_id == current_user.id,
            Booking.package_id == review_data.package_id,
            Booking.status == BookingStatus.COMPLETED
        )
        booking = session.exec(booking_statement).first()
        is_verified = booking is not None
    
    # Create review
    review = Review(
        user_id=current_user.id,
        package_id=review_data.package_id,
        booking_id=review_data.booking_id,
        rating=review_data.rating,
        comment_en=review_data.comment_en,
        comment_ar=review_data.comment_ar,
        is_verified=is_verified
    )
    
    session.add(review)
    
    # Update package rating
    # Calculate new average rating
    rating_stats = session.exec(
        select(func.avg(Review.rating), func.count(Review.id))
        .where(Review.package_id == review_data.package_id)
    ).first()
    
    current_avg = rating_stats[0] or 0
    current_count = rating_stats[1] or 0
    
    # Calculate new average including this review
    new_avg = ((current_avg * current_count) + review_data.rating) / (current_count + 1)
    new_count = current_count + 1
    
    package.rating = round(new_avg, 2)
    package.total_reviews = new_count
    
    session.commit()
    session.refresh(review)
    
    return APIResponse(
        success=True,
        message="Review created successfully",
        data={"review_id": review.id}
    )

@router.get("/my-reviews")
async def get_my_reviews(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get current user's reviews"""
    statement = select(Review).where(Review.user_id == current_user.id)
    reviews = session.exec(statement).all()
    
    response_reviews = []
    for review in reviews:
        # Get package details
        package_statement = select(Package).where(Package.id == review.package_id)
        package = session.exec(package_statement).first()
        
        response_reviews.append({
            "id": review.id,
            "package_id": review.package_id,
            "package_title": package.title_en if package else "Unknown Package",
            "rating": review.rating,
            "comment_en": review.comment_en,
            "comment_ar": review.comment_ar,
            "is_verified": review.is_verified,
            "created_at": review.created_at
        })
    
    return response_reviews

@router.put("/{review_id}", response_model=APIResponse)
async def update_review(
    review_id: int,
    review_data: ReviewCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Update a review"""
    statement = select(Review).where(Review.id == review_id)
    review = session.exec(statement).first()
    
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
    if review.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this review"
        )
    
    # Update review
    old_rating = review.rating
    review.rating = review_data.rating
    review.comment_en = review_data.comment_en
    review.comment_ar = review_data.comment_ar
    
    # Update package rating if rating changed
    if old_rating != review_data.rating:
        package_statement = select(Package).where(Package.id == review.package_id)
        package = session.exec(package_statement).first()
        
        if package:
            # Recalculate average rating
            rating_stats = session.exec(
                select(func.avg(Review.rating))
                .where(Review.package_id == review.package_id)
            ).first()
            
            package.rating = round(rating_stats[0] or 0, 2)
    
    session.commit()
    
    return APIResponse(
        success=True,
        message="Review updated successfully"
    )

@router.delete("/{review_id}", response_model=APIResponse)
async def delete_review(
    review_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Delete a review"""
    statement = select(Review).where(Review.id == review_id)
    review = session.exec(statement).first()
    
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
    if review.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this review"
        )
    
    package_id = review.package_id
    session.delete(review)
    
    # Update package rating
    package_statement = select(Package).where(Package.id == package_id)
    package = session.exec(package_statement).first()
    
    if package:
        # Recalculate rating and count
        rating_stats = session.exec(
            select(func.avg(Review.rating), func.count(Review.id))
            .where(Review.package_id == package_id)
        ).first()
        
        package.rating = round(rating_stats[0] or 0, 2)
        package.total_reviews = rating_stats[1] or 0
    
    session.commit()
    
    return APIResponse(
        success=True,
        message="Review deleted successfully"
    )