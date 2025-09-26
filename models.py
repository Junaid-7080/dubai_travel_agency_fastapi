from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime
from enum import Enum
import json

class UserRole(str, Enum):
    CUSTOMER = "customer"
    ADMIN = "admin"
    STAFF = "staff"

class BookingStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"

class PaymentStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"

class PaymentMethod(str, Enum):
    STRIPE = "stripe"
    PAYPAL = "paypal"
    PAYTABS = "paytabs"

class Language(str, Enum):
    EN = "en"
    AR = "ar"

# ===== User Model =====
class UserBase(SQLModel):
    name: str
    email: str
    mobile: Optional[str] = None
    language: Language = Language.EN
    role: UserRole = UserRole.CUSTOMER

class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    password_hash: str
    is_active: bool = True
    email_verified: bool = False
    mobile_verified: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    # Relationships
    bookings: List["Booking"] = Relationship(back_populates="user")
    reviews: List["Review"] = Relationship(back_populates="user")

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    email_verified: bool
    mobile_verified: bool
    created_at: datetime

# ===== Package Model =====
class PackageBase(SQLModel):
    title_en: str
    title_ar: str
    description_en: str
    description_ar: str
    price: float
    duration: str  # e.g., "8 hours", "2 days"
    max_travelers: int = 50
    min_travelers: int = 1
    includes_en: Optional[str] = None
    includes_ar: Optional[str] = None
    excludes_en: Optional[str] = None
    excludes_ar: Optional[str] = None

class Package(PackageBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    images: Optional[str] = None  # JSON array of image URLs
    availability: int = 100  # Available slots
    is_active: bool = True
    featured: bool = False
    rating: float = 0.0
    total_reviews: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    # Relationships
    bookings: List["Booking"] = Relationship(back_populates="package")
    reviews: List["Review"] = Relationship(back_populates="package")

class PackageCreate(PackageBase):
    images: Optional[List[str]] = None

class PackageUpdate(SQLModel):
    title_en: Optional[str] = None
    title_ar: Optional[str] = None
    description_en: Optional[str] = None
    description_ar: Optional[str] = None
    price: Optional[float] = None
    duration: Optional[str] = None
    max_travelers: Optional[int] = None
    min_travelers: Optional[int] = None
    includes_en: Optional[str] = None
    includes_ar: Optional[str] = None
    excludes_en: Optional[str] = None
    excludes_ar: Optional[str] = None
    availability: Optional[int] = None
    is_active: Optional[bool] = None
    featured: Optional[bool] = None

class PackageResponse(PackageBase):
    id: int
    images: Optional[List[str]] = None
    availability: int
    is_active: bool
    featured: bool
    rating: float
    total_reviews: int
    created_at: datetime

# ===== Booking Model =====
class BookingBase(SQLModel):
    travel_date: datetime
    travelers_count: int
    special_requests: Optional[str] = None
    traveler_details: Optional[str] = None  # JSON with traveler info

class Booking(BookingBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    package_id: int = Field(foreign_key="package.id")
    total_price: float
    status: BookingStatus = BookingStatus.PENDING
    payment_status: PaymentStatus = PaymentStatus.PENDING
    booking_reference: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    # Relationships
    user: User = Relationship(back_populates="bookings")
    package: Package = Relationship(back_populates="bookings")
    payments: List["Payment"] = Relationship(back_populates="booking")

class BookingCreate(BookingBase):
    package_id: int
    traveler_details: List[dict]  # List of traveler information

class BookingResponse(BookingBase):
    id: int
    user_id: int
    package_id: int
    total_price: float
    status: BookingStatus
    payment_status: PaymentStatus
    booking_reference: Optional[str]
    created_at: datetime
    package: Optional[PackageResponse] = None
    user: Optional[UserResponse] = None

# ===== Payment Model =====
class PaymentBase(SQLModel):
    amount: float
    currency: str = "AED"
    payment_method: PaymentMethod

class Payment(PaymentBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    booking_id: int = Field(foreign_key="booking.id")
    transaction_id: Optional[str] = None
    external_reference: Optional[str] = None
    status: PaymentStatus = PaymentStatus.PENDING
    failure_reason: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    
    # Relationships
    booking: Booking = Relationship(back_populates="payments")

class PaymentCreate(PaymentBase):
    booking_id: int

class PaymentResponse(PaymentBase):
    id: int
    booking_id: int
    transaction_id: Optional[str]
    external_reference: Optional[str]
    status: PaymentStatus
    failure_reason: Optional[str]
    created_at: datetime
    processed_at: Optional[datetime]

# ===== Review Model =====
class ReviewBase(SQLModel):
    rating: int = Field(ge=1, le=5)
    comment_en: Optional[str] = None
    comment_ar: Optional[str] = None

class Review(ReviewBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    package_id: int = Field(foreign_key="package.id")
    booking_id: Optional[int] = Field(foreign_key="booking.id")
    is_verified: bool = False  # Only verified if user actually booked
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    user: User = Relationship(back_populates="reviews")
    package: Package = Relationship(back_populates="reviews")

class ReviewCreate(ReviewBase):
    package_id: int
    booking_id: Optional[int] = None

class ReviewResponse(ReviewBase):
    id: int
    user_id: int
    package_id: int
    is_verified: bool
    created_at: datetime
    user_name: Optional[str] = None

# ===== OTP Model =====
class OTP(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    identifier: str  # email or mobile
    otp_code: str
    purpose: str  # registration, login, password_reset
    expires_at: datetime
    verified: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)