# ===== notification_service.py =====
from sqlmodel import Session, select
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from models import Notification, User, NotificationType, NotificationStatus
from schemas import NotificationCreate, NotificationResponse
import requests
import os
from config import settings

class NotificationService:
    def __init__(self, db: Session):
        self.db = db
    
    async def create_notification(self, notification_data: NotificationCreate) -> NotificationResponse:
        """Create a new notification"""
        # Convert data dict to JSON string if provided
        data_json = None
        if notification_data.data:
            data_json = json.dumps(notification_data.data)
        
        notification = Notification(
            title_en=notification_data.title_en,
            title_ar=notification_data.title_ar,
            message_en=notification_data.message_en,
            message_ar=notification_data.message_ar,
            notification_type=notification_data.notification_type,
            priority=notification_data.priority,
            user_id=notification_data.user_id,
            data=data_json,
            sent_at=datetime.utcnow() if notification_data.send_immediately else None
        )
        
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        
        # Send notification if immediately requested
        if notification_data.send_immediately:
            await self.send_notification(notification.id)
        
        return NotificationResponse(
            id=notification.id,
            title_en=notification.title_en,
            title_ar=notification.title_ar,
            message_en=notification.message_en,
            message_ar=notification.message_ar,
            notification_type=notification.notification_type,
            priority=notification.priority,
            user_id=notification.user_id,
            status=notification.status,
            sent_at=notification.sent_at,
            read_at=notification.read_at,
            created_at=notification.created_at,
            data=json.loads(notification.data) if notification.data else None
        )

    
    async def get_user_notifications(
        self, 
        user_id: int, 
        status: Optional[NotificationStatus] = None,
        notification_type: Optional[NotificationType] = None,
        page: int = 1,
        size: int = 20
    ) -> List[NotificationResponse]:
        """Get notifications for a specific user"""
        query = select(Notification).where(Notification.user_id == user_id)
        
        if status:
            query = query.where(Notification.status == status)
        if notification_type:
            query = query.where(Notification.notification_type == notification_type)
        
        query = query.order_by(Notification.created_at.desc())
        query = query.offset((page - 1) * size).limit(size)
        
        notifications = self.db.exec(query).all()
        
        return [
            NotificationResponse(
                id=n.id,
                title_en=n.title_en,
                title_ar=n.title_ar,
                message_en=n.message_en,
                message_ar=n.message_ar,
                notification_type=n.notification_type,
                priority=n.priority,
                user_id=n.user_id,
                status=n.status,
                sent_at=n.sent_at,
                read_at=n.read_at,
                created_at=n.created_at,
                data=json.loads(n.data) if n.data else None
            ) for n in notifications
        ]
    
    async def mark_as_read(self, notification_id: int, user_id: int) -> bool:
        """Mark a notification as read"""
        notification = self.db.get(Notification, notification_id)
        if not notification or notification.user_id != user_id:
            return False
        
        notification.status = NotificationStatus.READ
        notification.read_at = datetime.utcnow()
        self.db.commit()
        return True
    
    async def mark_all_as_read(self, user_id: int) -> int:
        """Mark all notifications as read for a user"""
        query = select(Notification).where(
            Notification.user_id == user_id,
            Notification.status == NotificationStatus.UNREAD
        )
        notifications = self.db.exec(query).all()
        
        count = 0
        for notification in notifications:
            notification.status = NotificationStatus.READ
            notification.read_at = datetime.utcnow()
            count += 1
        
        self.db.commit()
        return count
    
    async def get_unread_count(self, user_id: int) -> int:
        """Get count of unread notifications for a user"""
        query = select(Notification).where(
            Notification.user_id == user_id,
            Notification.status == NotificationStatus.UNREAD
        )
        notifications = self.db.exec(query).all()
        return len(notifications)
    
    async def send_notification(self, notification_id: int) -> bool:
        """Send notification via email/SMS/push"""
        notification = self.db.get(Notification, notification_id)
        if not notification:
            return False
        
        try:
            # Get user if notification is for specific user
            user = None
            if notification.user_id:
                user = self.db.get(User, notification.user_id)
            
            # Send email notification
            if user and user.email:
                await self._send_email_notification(notification, user)
            
            # Send SMS notification (if mobile is available)
            if user and user.mobile:
                await self._send_sms_notification(notification, user)
            
            # Update sent_at timestamp
            notification.sent_at = datetime.utcnow()
            self.db.commit()
            
            return True
        except Exception as e:
            print(f"Error sending notification {notification_id}: {e}")
            return False
    
    async def _send_email_notification(self, notification: Notification, user: User):
        """Send email notification"""
        try:
            # Choose language based on user preference
            title = notification.title_en if user.language == "en" else notification.title_ar
            message = notification.message_en if user.language == "en" else notification.message_ar
            
            # Create email content
            subject = f"Travel Agency Notification: {title}"
            body = f"""
            Dear {user.name},
            
            {message}
            
            Best regards,
            Dubai Travel Agency Team
            """
            
            # Send email (implement your email service)
            # This is a placeholder - implement with your email service
            print(f"Email sent to {user.email}: {subject}")
            
        except Exception as e:
            print(f"Error sending email to {user.email}: {e}")
    
    async def _send_sms_notification(self, notification: Notification, user: User):
        """Send SMS notification"""
        try:
            # Choose language based on user preference
            message = notification.message_en if user.language == "en" else notification.message_ar
            
            # Send SMS (implement your SMS service)
            # This is a placeholder - implement with your SMS service
            print(f"SMS sent to {user.mobile}: {message}")
            
        except Exception as e:
            print(f"Error sending SMS to {user.mobile}: {e}")
    
    async def create_booking_notification(
        self, 
        user_id: int, 
        booking_id: int, 
        notification_type: NotificationType,
        booking_data: Dict[str, Any]
    ) -> NotificationResponse:
        """Create booking-related notification"""
        templates = {
            NotificationType.BOOKING_CONFIRMED: {
                "en": {
                    "title": "Booking Confirmed!",
                    "message": f"Your booking #{booking_data.get('reference', booking_id)} has been confirmed. Travel date: {booking_data.get('travel_date', 'N/A')}"
                },
                "ar": {
                    "title": "تم تأكيد الحجز!",
                    "message": f"تم تأكيد حجزك رقم #{booking_data.get('reference', booking_id)}. تاريخ السفر: {booking_data.get('travel_date', 'N/A')}"
                }
            },
            NotificationType.BOOKING_CANCELLED: {
                "en": {
                    "title": "Booking Cancelled",
                    "message": f"Your booking #{booking_data.get('reference', booking_id)} has been cancelled."
                },
                "ar": {
                    "title": "تم إلغاء الحجز",
                    "message": f"تم إلغاء حجزك رقم #{booking_data.get('reference', booking_id)}."
                }
            }
        }
        
        template = templates.get(notification_type)
        if not template:
            raise ValueError(f"No template found for {notification_type}")
        
        notification_data = NotificationCreate(
            title_en=template["en"]["title"],
            title_ar=template["ar"]["title"],
            message_en=template["en"]["message"],
            message_ar=template["ar"]["message"],
            notification_type=notification_type,
            priority=3,  # High priority for booking notifications
            user_id=user_id,
            data=booking_data,
            send_immediately=True
        )
        
        return await self.create_notification(notification_data)
    
    async def create_payment_notification(
        self, 
        user_id: int, 
        payment_id: int, 
        notification_type: NotificationType,
        payment_data: Dict[str, Any]
    ) -> NotificationResponse:
        """Create payment-related notification"""
        templates = {
            NotificationType.PAYMENT_SUCCESS: {
                "en": {
                    "title": "Payment Successful!",
                    "message": f"Your payment of AED {payment_data.get('amount', 'N/A')} has been processed successfully."
                },
                "ar": {
                    "title": "تم الدفع بنجاح!",
                    "message": f"تم معالجة دفعتك بقيمة {payment_data.get('amount', 'N/A')} درهم إماراتي بنجاح."
                }
            },
            NotificationType.PAYMENT_FAILED: {
                "en": {
                    "title": "Payment Failed",
                    "message": f"Your payment of AED {payment_data.get('amount', 'N/A')} could not be processed. Please try again."
                },
                "ar": {
                    "title": "فشل في الدفع",
                    "message": f"لم يتم معالجة دفعتك بقيمة {payment_data.get('amount', 'N/A')} درهم إماراتي. يرجى المحاولة مرة أخرى."
                }
            }
        }
        
        template = templates.get(notification_type)
        if not template:
            raise ValueError(f"No template found for {notification_type}")
        
        notification_data = NotificationCreate(
            title_en=template["en"]["title"],
            title_ar=template["ar"]["title"],
            message_en=template["en"]["message"],
            message_ar=template["ar"]["message"],
            notification_type=notification_type,
            priority=3,  # High priority for payment notifications
            user_id=user_id,
            data=payment_data,
            send_immediately=True
        )
        
        return await self.create_notification(notification_data)
    
    async def create_broadcast_notification(
        self, 
        title_en: str, 
        title_ar: str, 
        message_en: str, 
        message_ar: str,
        notification_type: NotificationType = NotificationType.ADMIN_ANNOUNCEMENT,
        priority: int = 2
    ) -> NotificationResponse:
        """Create broadcast notification for all users"""
        notification_data = NotificationCreate(
            title_en=title_en,
            title_ar=title_ar,
            message_en=message_en,
            message_ar=message_ar,
            notification_type=notification_type,
            priority=priority,
            user_id=None,  # Broadcast to all users
            send_immediately=True
        )
        
        return await self.create_notification(notification_data)