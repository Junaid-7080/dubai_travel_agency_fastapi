# ===== schemas.py =====
from dataclasses import Field
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from models import Language, BookingStatus, PaymentStatus, PaymentMethod, UserRole

# Authentication Schemas
class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    mobile: Optional[str]
    password: str
    language: str = "en"
    role: Optional[UserRole] = UserRole.CUSTOMER   # 👈 default to CUSTOMER


class OTPRequest(BaseModel):
    identifier: str  # email or mobile
    purpose: str = "login"

class OTPVerify(BaseModel):
    identifier: str
    otp_code: str
    purpose: str = "login"

# Package Schemas
class PackageFilter(BaseModel):
    search: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    featured: Optional[bool] = None
    language: Language = Language.EN
    page: int = 1
    size: int = 10

# Booking Schemas
class TravelerInfo(BaseModel):
    name: str
    passport_number: Optional[str] = None
    nationality: Optional[str] = None
    date_of_birth: Optional[str] = None
    email: Optional[str] = None
    mobile: Optional[str] = None

class BookingRequest(BaseModel):
    package_id: int
    travel_date: datetime
    travelers_count: int
    traveler_details: List[TravelerInfo]
    special_requests: Optional[str] = None

# Payment Schemas
class PaymentRequest(BaseModel):
    booking_id: int
    payment_method: PaymentMethod
    return_url: Optional[str] = None

class PaymentConfirmation(BaseModel):
    transaction_id: str
    status: str
    external_reference: Optional[str] = None

# Admin Schemas
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
    notes: Optional[str] = None

class UserRoleUpdate(BaseModel):
    role: str  # "customer", "admin", "staff"

# User Response Schema
class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    mobile: Optional[str] = None
    language: Language
    role: str
    is_active: bool
    email_verified: bool = False
    mobile_verified: bool = False
    created_at: datetime

# Response Schemas
class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None
