# ===== routers/public.py =====
from fastapi import APIRouter, Depends
from sqlmodel import Session, select, func
from models import Package, Review
from database import get_session

router = APIRouter(prefix="/public", tags=["Public"])

@router.get("/featured-packages")
async def get_featured_packages(session: Session = Depends(get_session)):
    """Get featured packages (no authentication required)"""
    statement = select(Package).where(
        Package.is_active == True,
        Package.featured == True
    ).limit(6)
    
    packages = session.exec(statement).all()
    
    return [
        {
            "id": package.id,
            "title_en": package.title_en,
            "title_ar": package.title_ar,
            "price": package.price,
            "duration": package.duration,
            "rating": package.rating,
            "total_reviews": package.total_reviews,
            "images": package.images
        }
        for package in packages
    ]

@router.get("/stats")
async def get_public_stats(session: Session = Depends(get_session)):
    """Get public statistics"""
    total_packages = session.exec(
        select(func.count(Package.id)).where(Package.is_active == True)
    ).first() or 0
    
    total_reviews = session.exec(select(func.count(Review.id))).first() or 0
    
    avg_rating = session.exec(select(func.avg(Package.rating))).first() or 0
    
    return {
        "total_packages": total_packages,
        "total_reviews": total_reviews,
        "average_rating": round(avg_rating, 2) if avg_rating else 0,
        "languages_supported": ["English", "Arabic"]
    }