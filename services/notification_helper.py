# ===== notification_helper.py =====
from sqlmodel import Session
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import json

from models import User, Booking, Payment, NotificationType
from services.notification_service import NotificationService
from services.notification_templates import NotificationTemplates, COMMON_TEMPLATES

class NotificationHelper:
    """Helper class to automatically create notifications for various events"""
    
    def __init__(self, db: Session):
        self.db = db
        self.notification_service = NotificationService(db)
    
    async def send_booking_confirmation(self, booking: Booking) -> bool:
        """Send booking confirmation notification"""
        try:
            user = self.db.get(User, booking.user_id)
            if not user:
                return False
            
            # Get booking data for template
            booking_data = {
                "booking_id": booking.id,
                "reference": booking.booking_reference,
                "travel_date": booking.travel_date.strftime("%Y-%m-%d"),
                "package_title": booking.package.title_en if booking.package else "Travel Package",
                "total_price": booking.total_price,
                "travelers_count": booking.travelers_count
            }
            
            # Create notification
            await self.notification_service.create_booking_notification(
                user_id=user.id,
                booking_id=booking.id,
                notification_type=NotificationType.BOOKING_CONFIRMED,
                booking_data=booking_data
            )
            
            return True
        except Exception as e:
            print(f"Error sending booking confirmation: {e}")
            return False
    
    async def send_booking_cancellation(self, booking: Booking, reason: Optional[str] = None) -> bool:
        """Send booking cancellation notification"""
        try:
            user = self.db.get(User, booking.user_id)
            if not user:
                return False
            
            booking_data = {
                "booking_id": booking.id,
                "reference": booking.booking_reference,
                "travel_date": booking.travel_date.strftime("%Y-%m-%d"),
                "package_title": booking.package.title_en if booking.package else "Travel Package",
                "cancellation_reason": reason or "No reason provided"
            }
            
            await self.notification_service.create_booking_notification(
                user_id=user.id,
                booking_id=booking.id,
                notification_type=NotificationType.BOOKING_CANCELLED,
                booking_data=booking_data
            )
            
            return True
        except Exception as e:
            print(f"Error sending booking cancellation: {e}")
            return False
    
    async def send_payment_success(self, payment: Payment) -> bool:
        """Send payment success notification"""
        try:
            booking = self.db.get(Booking, payment.booking_id)
            if not booking:
                return False
            
            user = self.db.get(User, booking.user_id)
            if not user:
                return False
            
            payment_data = {
                "payment_id": payment.id,
                "amount": payment.amount,
                "currency": payment.currency,
                "payment_method": payment.payment_method.value,
                "transaction_id": payment.transaction_id,
                "booking_reference": booking.booking_reference
            }
            
            await self.notification_service.create_payment_notification(
                user_id=user.id,
                payment_id=payment.id,
                notification_type=NotificationType.PAYMENT_SUCCESS,
                payment_data=payment_data
            )
            
            return True
        except Exception as e:
            print(f"Error sending payment success: {e}")
            return False
    
    async def send_payment_failed(self, payment: Payment, failure_reason: Optional[str] = None) -> bool:
        """Send payment failure notification"""
        try:
            booking = self.db.get(Booking, payment.booking_id)
            if not booking:
                return False
            
            user = self.db.get(User, booking.user_id)
            if not user:
                return False
            
            payment_data = {
                "payment_id": payment.id,
                "amount": payment.amount,
                "currency": payment.currency,
                "payment_method": payment.payment_method.value,
                "failure_reason": failure_reason or payment.failure_reason,
                "booking_reference": booking.booking_reference
            }
            
            await self.notification_service.create_payment_notification(
                user_id=user.id,
                payment_id=payment.id,
                notification_type=NotificationType.PAYMENT_FAILED,
                payment_data=payment_data
            )
            
            return True
        except Exception as e:
            print(f"Error sending payment failure: {e}")
            return False
    
    async def send_welcome_notification(self, user: User) -> bool:
        """Send welcome notification to new users"""
        try:
            template = COMMON_TEMPLATES["welcome"]
            language = user.language.value if user.language else "en"
            
            notification_data = {
                "title_en": template["en"]["title"],
                "title_ar": template["ar"]["title"],
                "message_en": template["en"]["message"],
                "message_ar": template["ar"]["message"],
                "notification_type": NotificationType.ADMIN_ANNOUNCEMENT,
                "priority": 2,
                "user_id": user.id,
                "data": {"type": "welcome", "user_id": user.id},
                "send_immediately": True
            }
            
            await self.notification_service.create_notification(notification_data)
            return True
        except Exception as e:
            print(f"Error sending welcome notification: {e}")
            return False
    
    async def send_travel_reminder(self, booking: Booking, hours_before: int = 24) -> bool:
        """Send travel reminder notification"""
        try:
            user = self.db.get(User, booking.user_id)
            if not user:
                return False
            
            # Choose template based on hours before
            if hours_before == 1:
                template_key = "booking_reminder_1h"
            else:
                template_key = "booking_reminder_24h"
            
            template = COMMON_TEMPLATES[template_key]
            
            # Format template with booking details
            formatted_template = NotificationTemplates.format_template(
                template["en"],
                travel_date=booking.travel_date.strftime("%Y-%m-%d"),
                package_title=booking.package.title_en if booking.package else "Travel Package",
                meeting_point="Main Entrance"  # You can make this dynamic
            )
            
            notification_data = {
                "title_en": formatted_template["title"],
                "title_ar": template["ar"]["title"],
                "message_en": formatted_template["message"],
                "message_ar": template["ar"]["message"],
                "notification_type": NotificationType.REMINDER,
                "priority": 3,
                "user_id": user.id,
                "data": {
                    "type": "travel_reminder",
                    "booking_id": booking.id,
                    "hours_before": hours_before,
                    "travel_date": booking.travel_date.isoformat()
                },
                "send_immediately": True
            }
            
            await self.notification_service.create_notification(notification_data)
            return True
        except Exception as e:
            print(f"Error sending travel reminder: {e}")
            return False
    
    async def send_package_update(self, booking: Booking, update_details: str) -> bool:
        """Send package update notification"""
        try:
            user = self.db.get(User, booking.user_id)
            if not user:
                return False
            
            notification_data = {
                "title_en": "📦 Package Update",
                "title_ar": "📦 تحديث الحزمة",
                "message_en": f"Your package '{booking.package.title_en if booking.package else 'Travel Package'}' has been updated: {update_details}",
                "message_ar": f"تم تحديث حزمتك '{booking.package.title_ar if booking.package else 'حزمة السفر'}': {update_details}",
                "notification_type": NotificationType.PACKAGE_UPDATE,
                "priority": 2,
                "user_id": user.id,
                "data": {
                    "type": "package_update",
                    "booking_id": booking.id,
                    "update_details": update_details
                },
                "send_immediately": True
            }
            
            await self.notification_service.create_notification(notification_data)
            return True
        except Exception as e:
            print(f"Error sending package update: {e}")
            return False
    
    async def send_weather_update(self, booking: Booking, weather_info: str) -> bool:
        """Send weather update notification"""
        try:
            user = self.db.get(User, booking.user_id)
            if not user:
                return False
            
            template = COMMON_TEMPLATES["weather_update"]
            
            notification_data = {
                "title_en": template["en"]["title"],
                "title_ar": template["ar"]["title"],
                "message_en": f"{template['en']['message']} {weather_info}",
                "message_ar": f"{template['ar']['message']} {weather_info}",
                "notification_type": NotificationType.REMINDER,
                "priority": 2,
                "user_id": user.id,
                "data": {
                    "type": "weather_update",
                    "booking_id": booking.id,
                    "weather_info": weather_info,
                    "travel_date": booking.travel_date.isoformat()
                },
                "send_immediately": True
            }
            
            await self.notification_service.create_notification(notification_data)
            return True
        except Exception as e:
            print(f"Error sending weather update: {e}")
            return False
    
    async def send_promotional_notification(self, user: User, promotion_title: str, promotion_message: str) -> bool:
        """Send promotional notification"""
        try:
            notification_data = {
                "title_en": f"🎁 {promotion_title}",
                "title_ar": f"🎁 {promotion_title}",
                "message_en": promotion_message,
                "message_ar": promotion_message,  # You might want to translate this
                "notification_type": NotificationType.PROMOTION,
                "priority": 1,
                "user_id": user.id,
                "data": {
                    "type": "promotion",
                    "promotion_title": promotion_title
                },
                "send_immediately": True
            }
            
            await self.notification_service.create_notification(notification_data)
            return True
        except Exception as e:
            print(f"Error sending promotional notification: {e}")
            return False
    
    async def send_broadcast_announcement(self, title_en: str, title_ar: str, message_en: str, message_ar: str) -> bool:
        """Send broadcast announcement to all users"""
        try:
            await self.notification_service.create_broadcast_notification(
                title_en=title_en,
                title_ar=title_ar,
                message_en=message_en,
                message_ar=message_ar,
                notification_type=NotificationType.ADMIN_ANNOUNCEMENT,
                priority=3
            )
            return True
        except Exception as e:
            print(f"Error sending broadcast announcement: {e}")
            return False
