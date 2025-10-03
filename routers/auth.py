# ===== routers/auth.py =====
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from datetime import datetime, timedelta
from models import User, OTP
from schemas import Token, LoginRequest, RegisterRequest, OTPRequest, OTPVerify, APIResponse, UserResponse
from database import get_session
from auth import create_access_token, get_password_hash, verify_password, generate_otp, get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ---------------- Register User ----------------
@router.post("/register", response_model=APIResponse)
async def register_user(user_data: RegisterRequest, session: Session = Depends(get_session)):
    """Register a new user"""
    # Check if user already exists
    statement = select(User).where(User.email == user_data.email)
    existing_user = session.exec(statement).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    role = "USER"  # default role

    # For testing: assign ADMIN to specific email(s)
    admin_emails = [
        "admin@gmail.com", 
        "admin@dubaitravel.com",
        "superadmin@dubaitravel.com"
    ]

    if user_data.email.lower() in admin_emails:
        role = "ADMIN"

    # Create new user 
    user = User(
        name=user_data.name,
        email=user_data.email,
        mobile=user_data.mobile,
        language=user_data.language,
        password_hash=get_password_hash(user_data.password),
        role=role
    )

    session.add(user)
    session.commit()
    session.refresh(user)


    try:
        # Create a new notification service instance with the current session
        from services.notification_service import NotificationService
        notification_service_instance = NotificationService(session)
        await notification_service_instance.send_welcome_email(user.email, user.name)
    except Exception as e:
        logger.warning(f"Failed to send welcome email: {e}")

    return APIResponse(
        success=True,
        message=f"User registered successfully with role {role}",
        data={"user_id": user.id, "role": role}
    )


# ---------------- Login User ----------------
@router.post("/login", response_model=Token)
async def login(user_data: LoginRequest, session: Session = Depends(get_session)):
    """Login user with email and password"""
    statement = select(User).where(User.email == user_data.email)
    user = session.exec(statement).first()

    if not user or not verify_password(user_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is deactivated"
        )
     

   # Create access token with 'sub'
    access_token = create_access_token(data={"sub": user.email})

    return Token(
        access_token=access_token,
        token_type="bearer",
        user={
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "language": user.language
        }
    )


# ---------------- Request OTP ----------------
@router.post("/request-otp", response_model=APIResponse)
async def request_otp(otp_data: OTPRequest, session: Session = Depends(get_session)):
    """Request OTP for login or verification"""
    # Generate OTP
    otp_code = generate_otp()
    expires_at = datetime.utcnow() + timedelta(minutes=5)

    # Save OTP to database
    otp_record = OTP(
        identifier=otp_data.identifier,
        otp_code=otp_code,
        purpose=otp_data.purpose,
        expires_at=expires_at
    )

    session.add(otp_record)
    session.commit()

    # Determine if identifier is email or mobile
    method = "email" if "@" in otp_data.identifier else "sms"

    # Send OTP
    from services.notification_service import NotificationService
    notification_service_instance = NotificationService(session)
    sent = await notification_service_instance.send_otp(otp_data.identifier, otp_code, method)

    if not sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send OTP"
        )

    return APIResponse(
        success=True,
        message=f"OTP sent successfully to {otp_data.identifier}"
    )


# ---------------- Verify OTP ----------------
@router.post("/verify-otp", response_model=Token)
async def verify_otp(otp_data: OTPVerify, session: Session = Depends(get_session)):
    """Verify OTP and login user"""
    # Find valid OTP
    statement = select(OTP).where(
        OTP.identifier == otp_data.identifier,
        OTP.otp_code == otp_data.otp_code,
        OTP.purpose == otp_data.purpose,
        OTP.expires_at > datetime.utcnow(),
        OTP.verified == False
    )
    otp_record = session.exec(statement).first()

    if not otp_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP"
        )

    # Mark OTP as verified
    otp_record.verified = True
    session.commit()

    # Find or create user
    statement = select(User).where(User.email == otp_data.identifier)
    user = session.exec(statement).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Create access token with 'sub'
    access_token = create_access_token(data={"sub": user.email})

    return Token(
        access_token=access_token,
        token_type="bearer",
        user={
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "language": user.language
        }
    )


# ---------------- Get Current User ----------------
@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "mobile": current_user.mobile,
        "language": current_user.language,
        "role": current_user.role,
        "is_active": current_user.is_active,
        "email_verified": getattr(current_user, "email_verified", False),
        "mobile_verified": getattr(current_user, "mobile_verified", False),
        "created_at": current_user.created_at
    }
