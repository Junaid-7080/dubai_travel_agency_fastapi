# ===== notification_integration.py =====
"""
Example of how to integrate notifications into your existing endpoints
"""

from fastapi import Depends
from sqlmodel import Session
from database import get_session
from services.notification_helper import NotificationHelper
from models import Booking, Payment, User

# Example: Add to your booking confirmation endpoint
async def confirm_booking_example(booking_id: int, db: Session = Depends(get_session)):
    """Example of how to add notification to booking confirmation"""
    
    # Your existing booking confirmation logic
    booking = db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Update booking status
    booking.status = "confirmed"
    db.commit()
    
    # Send notification
    notification_helper = NotificationHelper(db)
    await notification_helper.send_booking_confirmation(booking)
    
    return {"message": "Booking confirmed", "booking": booking}

# Example: Add to your payment success endpoint
async def process_payment_success_example(payment_id: int, db: Session = Depends(get_session)):
    """Example of how to add notification to payment success"""
    
    # Your existing payment processing logic
    payment = db.get(Payment, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    # Update payment status
    payment.status = "paid"
    db.commit()
    
    # Send notification
    notification_helper = NotificationHelper(db)
    await notification_helper.send_payment_success(payment)
    
    return {"message": "Payment processed", "payment": payment}

# Example: Add to your user registration endpoint
async def register_user_example(user_data: dict, db: Session = Depends(get_session)):
    """Example of how to add welcome notification to user registration"""
    
    # Your existing user registration logic
    user = User(**user_data)
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Send welcome notification
    notification_helper = NotificationHelper(db)
    await notification_helper.send_welcome_notification(user)
    
    return {"message": "User registered", "user": user}

# Example: Scheduled task for travel reminders
async def send_travel_reminders_example(db: Session):
    """Example of how to send travel reminders (can be run as a scheduled task)"""
    
    from datetime import datetime, timedelta
    
    # Get bookings for tomorrow
    tomorrow = datetime.now() + timedelta(days=1)
    bookings = db.query(Booking).filter(
        Booking.travel_date.date() == tomorrow.date(),
        Booking.status == "confirmed"
    ).all()
    
    notification_helper = NotificationHelper(db)
    
    for booking in bookings:
        await notification_helper.send_travel_reminder(booking, hours_before=24)
    
    return {"message": f"Sent reminders for {len(bookings)} bookings"}

# Example: Admin broadcast notification
async def send_admin_announcement_example(
    title_en: str,
    title_ar: str, 
    message_en: str,
    message_ar: str,
    db: Session = Depends(get_session)
):
    """Example of how to send admin announcements"""
    
    notification_helper = NotificationHelper(db)
    await notification_helper.send_broadcast_announcement(
        title_en=title_en,
        title_ar=title_ar,
        message_en=message_en,
        message_ar=message_ar
    )
    
    return {"message": "Announcement sent to all users"}

# Example: Weather update notification
async def send_weather_update_example(
    booking_id: int,
    weather_info: str,
    db: Session = Depends(get_session)
):
    """Example of how to send weather updates"""
    
    booking = db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    notification_helper = NotificationHelper(db)
    await notification_helper.send_weather_update(booking, weather_info)
    
    return {"message": "Weather update sent"}

# Example: Package update notification
async def send_package_update_example(
    booking_id: int,
    update_details: str,
    db: Session = Depends(get_session)
):
    """Example of how to send package updates"""
    
    booking = db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    notification_helper = NotificationHelper(db)
    await notification_helper.send_package_update(booking, update_details)
    
    return {"message": "Package update sent"}
