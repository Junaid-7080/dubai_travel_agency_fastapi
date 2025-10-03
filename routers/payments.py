# ===== routers/payments.py =====
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from models import Payment, PaymentCreate, PaymentResponse, Booking, BookingStatus, PaymentStatus, PaymentMethod
from schemas import PaymentRequest, PaymentConfirmation, APIResponse
from database import get_session
from auth import get_current_user
from services.payment_service import payment_service
from datetime import datetime
import json

router = APIRouter(prefix="/payments", tags=["Payments"])

@router.post("/create", response_model=APIResponse)
async def create_payment(
    payment_data: PaymentRequest,
    current_user = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Create payment for booking"""
    # Get booking
    statement = select(Booking).where(Booking.id == payment_data.booking_id)
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
            detail="Not authorized to pay for this booking"
        )
    
    # Check if payment already exists and is successful
    existing_payment = session.exec(
        select(Payment).where(
            Payment.booking_id == payment_data.booking_id,
            Payment.status == PaymentStatus.PAID
        )
    ).first()
    
    if existing_payment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment already completed for this booking"
        )
    
    # Create payment record
    payment = Payment(
        booking_id=payment_data.booking_id,
        amount=booking.total_price,
        currency="AED",
        payment_method=payment_data.payment_method
    )
    
    session.add(payment)
    session.commit()
    session.refresh(payment)
    
    # Process payment based on method
    metadata = {
        "booking_id": booking.id,
        "booking_reference": booking.booking_reference,
        "user_id": current_user.id,
        "email": current_user.email
    }
    
    payment_result = await payment_service.process_payment(
        payment_data.payment_method,
        booking.total_price,
        metadata
    )
    
    if not payment_result["success"]:
        payment.status = PaymentStatus.FAILED
        payment.failure_reason = payment_result.get("error", "Unknown error")
        session.commit()
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment failed: {payment_result.get('error', 'Unknown error')}"
        )
    
    # Update payment with external reference
    if payment_data.payment_method == PaymentMethod.STRIPE:
        payment.external_reference = payment_result.get("payment_intent_id")
    elif payment_data.payment_method == PaymentMethod.PAYPAL:
        payment.external_reference = payment_result.get("order_id")
    elif payment_data.payment_method == PaymentMethod.PAYTABS:
        payment.external_reference = payment_result.get("tran_ref")
    
    session.commit()
    
    response_data = {
        "payment_id": payment.id,
        "amount": payment.amount,
        "currency": payment.currency
    }
    
    # Add method-specific data
    if payment_data.payment_method == PaymentMethod.STRIPE:
        response_data["client_secret"] = payment_result.get("client_secret")
    elif payment_data.payment_method == PaymentMethod.PAYPAL:
        response_data["approval_url"] = payment_result.get("approval_url")
    elif payment_data.payment_method == PaymentMethod.PAYTABS:
        response_data["payment_url"] = payment_result.get("payment_url")
    
    return APIResponse(
        success=True,
        message="Payment initiated successfully",
        data=response_data
    )

