# ===== routers/auth.py =====
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from datetime import datetime, timedelta
from models import User, OTP, UserRole
from schemas import Token, LoginRequest, RegisterRequest, OTPRequest, OTPVerify, APIResponse, UserResponse
from database import get_session
from auth import create_access_token, get_password_hash, verify_password, generate_otp, get_current_user
from services.notification_service import notification_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


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

    # Create new user (role will default to CUSTOMER)
    user = User(
        name=user_data.name,
        email=user_data.email,
        mobile=user_data.mobile,
        language=user_data.language,
        password_hash=get_password_hash(user_data.password),
        role=UserRole.CUSTOMER,  # Explicitly set as CUSTOMER
        is_active=True,
        email_verified=False,  # Regular users need to verify email
        mobile_verified=False   # Regular users need to verify mobile
    )

    session.add(user)
    session.commit()
    session.refresh(user)

    # Send welcome email (optional)
    try:
        await notification_service.send_email(
            user.email,
            "Welcome to Dubai Travel Agency",
            "welcome_email",
            {"user_name": user.name, "user_language": user.language}
        )
    except Exception as e:
        logger.warning(f"Failed to send welcome email: {e}")

    return APIResponse(
        success=True,
        message="User registered successfully",
        data={
            "user_id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "language": user.language,
            "email_verified": user.email_verified,
            "note": "Please check your email for verification instructions"
        }
    )
# ---------------- Login User ----------------
@router.post("/login", response_model=Token)
async def login(user_data: LoginRequest, session: Session = Depends(get_session)):
    """Login user with email and password"""

    # Fetch user by email
    statement = select(User).where(User.email == user_data.email)
    user = session.exec(statement).first()

    # Check if user exists and password is correct
    if not user or not verify_password(user_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Check account status
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )

    # (Optional) Check if email verification is required
    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified"
        )

    # Create access token (use user.id as subject for uniqueness)
    access_token = create_access_token(data={"sub": str(user.id)})

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
    sent = await notification_service.send_otp(otp_data.identifier, otp_code, method)

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
