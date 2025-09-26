# ===== routers/packages.py =====
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlmodel import Session, select, func
from typing import List, Optional
from models import Package, PackageCreate, PackageUpdate, PackageResponse, Review, Language
from schemas import PackageFilter, APIResponse
from database import get_session
from auth import get_current_user, get_admin_user
from utils import save_uploaded_file, serialize_images, deserialize_images, get_localized_content
import json
from datetime import datetime

router = APIRouter(prefix="/packages", tags=["Packages"])

@router.get("/", response_model=List[PackageResponse])
async def get_packages(
    search: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    featured: Optional[bool] = None,
    lang: Language = Language.EN,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=50),
    session: Session = Depends(get_session)
):
    """Get packages with filters and pagination"""
    statement = select(Package).where(Package.is_active == True)
    
    # Apply filters
    if search:
        if lang == Language.AR:
            statement = statement.where(Package.title_ar.contains(search))
        else:
            statement = statement.where(Package.title_en.contains(search))
    
    if min_price is not None:
        statement = statement.where(Package.price >= min_price)
    
    if max_price is not None:
        statement = statement.where(Package.price <= max_price)
    
    if featured is not None:
        statement = statement.where(Package.featured == featured)
    
    # Apply pagination
    offset = (page - 1) * size
    statement = statement.offset(offset).limit(size)
    
    packages = session.exec(statement).all()
    
    # Convert to response format
    response_packages = []
    for package in packages:
        package_response = PackageResponse(
            id=package.id,
            title_en=package.title_en,
            title_ar=package.title_ar,
            description_en=package.description_en,
            description_ar=package.description_ar,
            price=package.price,
            duration=package.duration,
            max_travelers=package.max_travelers,
            min_travelers=package.min_travelers,
            includes_en=package.includes_en,
            includes_ar=package.includes_ar,
            excludes_en=package.excludes_en,
            excludes_ar=package.excludes_ar,
            images=deserialize_images(package.images),
            availability=package.availability,
            is_active=package.is_active,
            featured=package.featured,
            rating=package.rating,
            total_reviews=package.total_reviews,
            created_at=package.created_at
        )
        response_packages.append(package_response)
    
    return response_packages

@router.get("/{package_id}", response_model=PackageResponse)
async def get_package(
    package_id: int,
    lang: Language = Language.EN,
    session: Session = Depends(get_session)
):
    """Get package details by ID"""
    statement = select(Package).where(Package.id == package_id, Package.is_active == True)
    package = session.exec(statement).first()
    
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Package not found"
        )
    
    return PackageResponse(
        id=package.id,
        title_en=package.title_en,
        title_ar=package.title_ar,
        description_en=package.description_en,
        description_ar=package.description_ar,
        price=package.price,
        duration=package.duration,
        max_travelers=package.max_travelers,
        min_travelers=package.min_travelers,
        includes_en=package.includes_en,
        includes_ar=package.includes_ar,
        excludes_en=package.excludes_en,
        excludes_ar=package.excludes_ar,
        images=deserialize_images(package.images),
        availability=package.availability,
        is_active=package.is_active,
        featured=package.featured,
        rating=package.rating,
        total_reviews=package.total_reviews,
        created_at=package.created_at
    )

@router.get("/{package_id}/reviews")
async def get_package_reviews(
    package_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=50),
    session: Session = Depends(get_session)
):
    """Get reviews for a specific package"""
    offset = (page - 1) * size
    
    statement = select(Review).where(Review.package_id == package_id).offset(offset).limit(size)
    reviews = session.exec(statement).all()
    
    return [
        {
            "id": review.id,
            "rating": review.rating,
            "comment_en": review.comment_en,
            "comment_ar": review.comment_ar,
            "user_name": "Anonymous",  # Privacy protection
            "is_verified": review.is_verified,
            "created_at": review.created_at
        }
        for review in reviews
    ]

# Admin routes for package management
@router.post("/", response_model=APIResponse)
async def create_package(
    package_data: PackageCreate,
    current_user = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Create new package (Admin only)"""
    package = Package(
        title_en=package_data.title_en,
        title_ar=package_data.title_ar,
        description_en=package_data.description_en,
        description_ar=package_data.description_ar,
        price=package_data.price,
        duration=package_data.duration,
        max_travelers=package_data.max_travelers,
        min_travelers=package_data.min_travelers,
        includes_en=package_data.includes_en,
        includes_ar=package_data.includes_ar,
        excludes_en=package_data.excludes_en,
        excludes_ar=package_data.excludes_ar,
        images=serialize_images(package_data.images)
    )
    
    session.add(package)
    session.commit()
    session.refresh(package)
    
    return APIResponse(
        success=True,
        message="Package created successfully",
        data={"package_id": package.id}
    )

@router.put("/{package_id}", response_model=APIResponse)
async def update_package(
    package_id: int,
    package_data: PackageUpdate,
    current_user = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Update package (Admin only)"""
    statement = select(Package).where(Package.id == package_id)
    package = session.exec(statement).first()
    
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Package not found"
        )
    
    # Update fields
    update_data = package_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(package, field, value)
    
    package.updated_at = datetime.utcnow()
    session.commit()
    
    return APIResponse(
        success=True,
        message="Package updated successfully"
    )

@router.post("/{package_id}/images", response_model=APIResponse)
async def upload_package_images(
    package_id: int,
    files: List[UploadFile] = File(...),
    current_user = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Upload images for package (Admin only)"""
    statement = select(Package).where(Package.id == package_id)
    package = session.exec(statement).first()
    
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Package not found"
        )
    
    # Upload files
    uploaded_files = []
    for file in files:
        if not file.content_type.startswith('image/'):
            continue
        
        file_path = save_uploaded_file(file, "packages")
        uploaded_files.append(file_path)
    
    # Update package images
    current_images = deserialize_images(package.images) or []
    current_images.extend(uploaded_files)
    package.images = serialize_images(current_images)
    
    session.commit()
    
    return APIResponse(
        success=True,
        message=f"{len(uploaded_files)} images uploaded successfully",
        data={"uploaded_files": uploaded_files}
    )

@router.delete("/{package_id}", response_model=APIResponse)
async def delete_package(
    package_id: int,
    current_user = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Soft delete package (Admin only)"""
    statement = select(Package).where(Package.id == package_id)
    package = session.exec(statement).first()
    
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Package not found"
        )
    
    package.is_active = False
    package.updated_at = datetime.utcnow()
    session.commit()
    
    return APIResponse(
        success=True,
        message="Package deleted successfully"
    )
