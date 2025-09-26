# ===== routers/bookings.py =====
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List
from datetime import datetime
from models import Booking, BookingCreate, BookingResponse, Package, User, BookingStatus, PaymentStatus
from schemas import BookingRequest, APIResponse, TravelerInfo
from database import get_session
from auth import get_current_user, get_admin_user, generate_booking_reference
from services.notification_service import notification_service
import json

router = APIRouter(prefix="/bookings", tags=["Bookings"])

@router.post("/", response_model=APIResponse)
async def create_booking(
    booking_data: BookingRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Create a new booking"""
    # Get package
    statement = select(Package).where(Package.id == booking_data.package_id, Package.is_active == True)
    package = session.exec(statement).first()
    
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Package not found"
        )
    
    # Validate travelers count
    if booking_data.travelers_count < package.min_travelers or booking_data.travelers_count > package.max_travelers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Travelers count must be between {package.min_travelers} and {package.max_travelers}"
        )
    
    # Check availability
    if package.availability < booking_data.travelers_count:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not enough availability for this package"
        )
    
    # Calculate total price
    total_price = package.price * booking_data.travelers_count
    
    # Create booking
    booking = Booking(
        user_id=current_user.id,
        package_id=booking_data.package_id,
        travel_date=booking_data.travel_date,
        travelers_count=booking_data.travelers_count,
        total_price=total_price,
        special_requests=booking_data.special_requests,
        traveler_details=json.dumps([traveler.dict() for traveler in booking_data.traveler_details]),
        booking_reference=generate_booking_reference()
    )
    
    session.add(booking)
    
    # Update package availability
    package.availability -= booking_data.travelers_count
    
    session.commit()
    session.refresh(booking)
    
    return APIResponse(
        success=True,
        message="Booking created successfully",
        data={
            "booking_id": booking.id,
            "booking_reference": booking.booking_reference,
            "total_price": total_price
        }
    )

@router.get("/", response_model=List[BookingResponse])
async def get_user_bookings(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get current user's bookings"""
    statement = select(Booking).where(Booking.user_id == current_user.id)
    bookings = session.exec(statement).all()
    
    response_bookings = []
    for booking in bookings:
        # Get package details
        package_statement = select(Package).where(Package.id == booking.package_id)
        package = session.exec(package_statement).first()
        
        booking_response = BookingResponse(
            id=booking.id,
            user_id=booking.user_id,
            package_id=booking.package_id,
            travel_date=booking.travel_date,
            travelers_count=booking.travelers_count,
            total_price=booking.total_price,
            status=booking.status,
            payment_status=booking.payment_status,
            booking_reference=booking.booking_reference,
            special_requests=booking.special_requests,
            traveler_details=booking.traveler_details,
            created_at=booking.created_at,
            package={
                "id": package.id,
                "title_en": package.title_en,
                "title_ar": package.title_ar,
                "price": package.price,
                "duration": package.duration
            } if package else None
        )
        response_bookings.append(booking_response)
    
    return response_bookings

@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get specific booking details"""
    statement = select(Booking).where(Booking.id == booking_id)
    booking = session.exec(statement).first()
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    # Check if user owns the booking or is admin
    if booking.user_id != current_user.id and current_user.role not in ["admin", "staff"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this booking"
        )
    
    # Get package and user details
    package_statement = select(Package).where(Package.id == booking.package_id)
    package = session.exec(package_statement).first()
    
    user_statement = select(User).where(User.id == booking.user_id)
    user = session.exec(user_statement).first()
    
    return BookingResponse(
        id=booking.id,
        user_id=booking.user_id,
        package_id=booking.package_id,
        travel_date=booking.travel_date,
        travelers_count=booking.travelers_count,
        total_price=booking.total_price,
        status=booking.status,
        payment_status=booking.payment_status,
        booking_reference=booking.booking_reference,
        special_requests=booking.special_requests,
        traveler_details=booking.traveler_details,
        created_at=booking.created_at,
        package={
            "id": package.id,
            "title_en": package.title_en,
            "title_ar": package.title_ar,
            "price": package.price,
            "duration": package.duration,
            "images": json.loads(package.images) if package.images else []
        } if package else None,
        user={
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "mobile": user.mobile,
            "language": user.language
        } if user else None
    )

@router.put("/{booking_id}/cancel", response_model=APIResponse)
async def cancel_booking(
    booking_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Cancel a booking"""
    statement = select(Booking).where(Booking.id == booking_id)
    booking = session.exec(statement).first()
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    # Check ownership
    if booking.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to cancel this booking"
        )
    
    # Check if booking can be cancelled
    if booking.status in [BookingStatus.CANCELLED, BookingStatus.COMPLETED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Booking cannot be cancelled"
        )
    
    # Update booking status
    booking.status = BookingStatus.CANCELLED
    booking.updated_at = datetime.utcnow()
    
    # Restore package availability
    package_statement = select(Package).where(Package.id == booking.package_id)
    package = session.exec(package_statement).first()
    if package:
        package.availability += booking.travelers_count
        
    
    session.commit()
    
    
    # Send cancellation notification
    try:
        notification_data = {
            "user_name": current_user.name,
            "user_email": current_user.email,
            "user_mobile": current_user.mobile,
            "booking_reference": booking.booking_reference,
            "package_title": package.title_en if package else "Unknown Package"
        }
        
        await notification_service.send_email(
            current_user.email,
            "Booking Cancelled - Dubai Travel Agency",
            "booking_cancellation",
            notification_data
        )
    except Exception as e:
        # Log but don't fail the cancellation
        pass
    
    return APIResponse(
        success=True,
        message="Booking cancelled successfully"
    )
      