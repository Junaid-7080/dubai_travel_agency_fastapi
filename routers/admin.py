# routers/admin.py - Complete Admin System
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session, select, func, and_, or_, desc, asc
from datetime import datetime, timedelta, date
from typing import List, Optional, Dict, Any, Union
import logging
from pydantic import BaseModel, Field, EmailStr
from enum import Enum

# Import your existing models and dependencies
from database import get_session
from models import User, Package, Booking, Payment, Review, OTP, BookingStatus, PaymentStatus, UserRole
from auth import get_current_user, get_admin_user, get_password_hash, verify_password
from schemas import APIResponse

# Admin-specific models
class DashboardStats(BaseModel):
    total_bookings: int
    total_revenue: float
    pending_bookings: int
    active_packages: int
    total_users: int
    bookings_today: int
    revenue_today: float

class BookingUpdateStatus(BaseModel):
    status: BookingStatus

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    current_user = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Get dashboard statistics"""
    today = datetime.utcnow().date()
    
    # Total bookings
    total_bookings = session.exec(select(func.count(Booking.id))).first() or 0
    
    # Total revenue
    total_revenue = session.exec(
        select(func.sum(Payment.amount))
        .where(Payment.status == PaymentStatus.PAID)
    ).first() or 0.0
    
    # Pending bookings
    pending_bookings = session.exec(
        select(func.count(Booking.id))
        .where(Booking.status == BookingStatus.PENDING)
    ).first() or 0
    
    # Active packages
    active_packages = session.exec(
        select(func.count(Package.id))
        .where(Package.is_active == True)
    ).first() or 0
    
    # Total users
    total_users = session.exec(select(func.count(User.id))).first() or 0
    
    # Today's bookings
    bookings_today = session.exec(
        select(func.count(Booking.id))
        .where(func.date(Booking.created_at) == today)
    ).first() or 0
    
    # Today's revenue
    revenue_today = session.exec(
        select(func.sum(Payment.amount))
        .where(
            Payment.status == PaymentStatus.PAID,
            func.date(Payment.processed_at) == today
        )
    ).first() or 0.0
    
    return DashboardStats(
        total_bookings=total_bookings,
        total_revenue=total_revenue,
        pending_bookings=pending_bookings,
        active_packages=active_packages,
        total_users=total_users,
        bookings_today=bookings_today,
        revenue_today=revenue_today
    )

@router.get("/bookings")
async def get_all_bookings(
    status: Optional[BookingStatus] = None,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=50),
    current_user = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Get all bookings with filters"""
    statement = select(Booking)
    
    if status:
        statement = statement.where(Booking.status == status)
    
    offset = (page - 1) * size
    statement = statement.offset(offset).limit(size)
    
    bookings = session.exec(statement).all()
    
    # Get additional details for each booking
    response_bookings = []
    for booking in bookings:
        # Get user and package details
        user_statement = select(User).where(User.id == booking.user_id)
        user = session.exec(user_statement).first()
        
        package_statement = select(Package).where(Package.id == booking.package_id)
        package = session.exec(package_statement).first()
        
        response_bookings.append({
            "id": booking.id,
            "booking_reference": booking.booking_reference,
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "mobile": user.mobile
            } if user else None,
            "package": {
                "id": package.id,
                "title_en": package.title_en,
                "title_ar": package.title_ar,
                "price": package.price
            } if package else None,
            "travel_date": booking.travel_date,
            "travelers_count": booking.travelers_count,
            "total_price": booking.total_price,
            "status": booking.status,
            "payment_status": booking.payment_status,
            "created_at": booking.created_at,
            "special_requests": booking.special_requests
        })
    
    return response_bookings

@router.put("/bookings/{booking_id}/status", response_model=APIResponse)
async def update_booking_status(
    booking_id: int,
    status_data: BookingUpdateStatus,
    current_user = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Update booking status"""
    statement = select(Booking).where(Booking.id == booking_id)
    booking = session.exec(statement).first()
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    booking.status = status_data.status
    booking.updated_at = datetime.utcnow()
    
    session.commit()
    
    return APIResponse(
        success=True,
        message=f"Booking status updated to {status_data.status}"
    )

@router.get("/users")
async def get_all_users(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=50),
    current_user = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Get all users"""
    offset = (page - 1) * size
    statement = select(User).offset(offset).limit(size)
    users = session.exec(statement).all()
    
    response_users = []
    for user in users:
        # Get booking count for each user
        booking_count = session.exec(
            select(func.count(Booking.id)).where(Booking.user_id == user.id)
        ).first() or 0
        
        response_users.append({
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "mobile": user.mobile,
            "language": user.language,
            "role": user.role,
            "is_active": user.is_active,
            "email_verified": user.email_verified,
            "mobile_verified": user.mobile_verified,
            "created_at": user.created_at,
            "total_bookings": booking_count
        })
    
    return response_users

@router.get("/users/{user_id}/bookings")
async def get_user_bookings(
    user_id: int,
    current_user = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Get bookings for a specific user"""
    # Check if user exists
    user_statement = select(User).where(User.id == user_id)
    user = session.exec(user_statement).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get user's bookings
    statement = select(Booking).where(Booking.user_id == user_id)
    bookings = session.exec(statement).all()
    
    response_bookings = []
    for booking in bookings:
        package_statement = select(Package).where(Package.id == booking.package_id)
        package = session.exec(package_statement).first()
        
        response_bookings.append({
            "id": booking.id,
            "booking_reference": booking.booking_reference,
            "package": {
                "id": package.id,
                "title_en": package.title_en,
                "title_ar": package.title_ar,
                "price": package.price
            } if package else None,
            "travel_date": booking.travel_date,
            "travelers_count": booking.travelers_count,
            "total_price": booking.total_price,
            "status": booking.status,
            "payment_status": booking.payment_status,
            "created_at": booking.created_at
        })
    
    return response_bookings

@router.get("/reports/revenue")
async def get_revenue_report(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Get revenue report"""
    statement = select(func.sum(Payment.amount), func.count(Payment.id)).where(
        Payment.status == PaymentStatus.PAID
    )
    
    if start_date:
        start = datetime.fromisoformat(start_date)
        statement = statement.where(Payment.processed_at >= start)
    
    if end_date:
        end = datetime.fromisoformat(end_date)
        statement = statement.where(Payment.processed_at <= end)
    
    result = session.exec(statement).first()
    total_revenue = result[0] or 0.0
    total_transactions = result[1] or 0
    
    # Get revenue by payment method
    payment_methods = session.exec(
        select(Payment.payment_method, func.sum(Payment.amount))
        .where(Payment.status == PaymentStatus.PAID)
        .group_by(Payment.payment_method)
    ).all()
    
    revenue_by_method = {method: amount for method, amount in payment_methods}
    
    return {
        "total_revenue": total_revenue,
        "total_transactions": total_transactions,
        "revenue_by_method": revenue_by_method,
        "period": {
            "start_date": start_date,
            "end_date": end_date
        }
    }

@router.get("/reports/bookings")
async def get_bookings_report(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Get bookings report"""
    statement = select(func.count(Booking.id))
    
    if start_date:
        start = datetime.fromisoformat(start_date)
        statement = statement.where(Booking.created_at >= start)
    
    if end_date:
        end = datetime.fromisoformat(end_date)
        statement = statement.where(Booking.created_at <= end)
    
    total_bookings = session.exec(statement).first() or 0
    
    # Get bookings by status
    status_stats = session.exec(
        select(Booking.status, func.count(Booking.id))
        .group_by(Booking.status)
    ).all()
    
    bookings_by_status = {status.value: count for status, count in status_stats}
    
    # Get popular packages
    popular_packages = session.exec(
        select(Package.title_en, func.count(Booking.id))
        .join(Booking)
        .group_by(Package.id, Package.title_en)
        .order_by(func.count(Booking.id).desc())
        .limit(5)
    ).all()
    
    return {
        "total_bookings": total_bookings,
        "bookings_by_status": bookings_by_status,
        "popular_packages": [
            {"package_name": name, "booking_count": count}
            for name, count in popular_packages
        ],
        "period": {
            "start_date": start_date,
            "end_date": end_date
        }
    }