# ===== schemas.py =====
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from models import Language, BookingStatus, PaymentStatus, PaymentMethod, NotificationType, NotificationStatus

# Authentication Schemas
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: Optional[int] = None  # Add this
    user: Dict[str, Any]

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    mobile: Optional[str] = None
    password: str
    language: Language = Language.EN

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

# Notification Schemas
class NotificationCreate(BaseModel):
    title_en: str
    title_ar: str
    message_en: str
    message_ar: str
    notification_type: NotificationType
    priority: int = 1
    user_id: Optional[int] = None  # None for broadcast
    data: Optional[Dict[str, Any]] = None
    send_immediately: bool = True

class NotificationResponse(BaseModel):
    id: int
    title_en: str
    title_ar: str
    message_en: str
    message_ar: str
    notification_type: NotificationType
    priority: int
    user_id: Optional[int]
    status: NotificationStatus
    sent_at: Optional[datetime]
    read_at: Optional[datetime]
    created_at: datetime
    data: Optional[Dict[str, Any]] = None

class NotificationUpdate(BaseModel):
    status: Optional[NotificationStatus] = None
    read_at: Optional[datetime] = None

class NotificationFilter(BaseModel):
    notification_type: Optional[NotificationType] = None
    status: Optional[NotificationStatus] = None
    priority: Optional[int] = None
    user_id: Optional[int] = None
    page: int = 1
    size: int = 20

class NotificationStats(BaseModel):
    total_notifications: int
    unread_count: int
    read_count: int
    archived_count: int
    by_type: Dict[str, int]

class BulkNotificationUpdate(BaseModel):
    notification_ids: List[int]
    status: NotificationStatus

# Customer Schemas
class CustomerCreate(BaseModel):
    name: str
    email: str
    mobile: str
    nationality: str
    passport_number: str
    passport_expiry: datetime
    date_of_birth: datetime
    gender: str  # "male", "female", "other"
    address: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    language: Language = Language.EN

class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    mobile: Optional[str] = None
    nationality: Optional[str] = None
    passport_number: Optional[str] = None
    passport_expiry: Optional[datetime] = None
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    language: Optional[Language] = None
    is_active: Optional[bool] = None

class CustomerResponse(BaseModel):
    id: int
    name: str
    email: str
    mobile: str
    nationality: str
    passport_number: str
    passport_expiry: datetime
    date_of_birth: datetime
    gender: str
    address: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    language: Language
    is_active: bool
    user_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

class CustomerFilter(BaseModel):
    search: Optional[str] = None
    nationality: Optional[str] = None
    is_active: Optional[bool] = None
    language: Optional[Language] = None
    page: int = 1
    size: int = 20

class CustomerStats(BaseModel):
    total_customers: int
    active_customers: int
    inactive_customers: int
    customers_by_nationality: Dict[str, int]
    customers_by_language: Dict[str, int]

# Response Schemas
class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None
