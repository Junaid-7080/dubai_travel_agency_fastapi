# ===== notification_templates.py =====
from typing import Dict, Any
from models import NotificationType

class NotificationTemplates:
    """Templates for different types of notifications"""
    
    @staticmethod
    def get_booking_templates() -> Dict[str, Dict[str, str]]:
        """Templates for booking-related notifications"""
        return {
            NotificationType.BOOKING_CONFIRMED: {
                "en": {
                    "title": "🎉 Booking Confirmed!",
                    "message": "Your booking has been confirmed successfully. We're excited to have you join us on this amazing journey!"
                },
                "ar": {
                    "title": "🎉 تم تأكيد الحجز!",
                    "message": "تم تأكيد حجزك بنجاح. نحن متحمسون لانضمامك إلينا في هذه الرحلة المذهلة!"
                }
            },
            NotificationType.BOOKING_CANCELLED: {
                "en": {
                    "title": "❌ Booking Cancelled",
                    "message": "Your booking has been cancelled. If you have any questions, please contact our support team."
                },
                "ar": {
                    "title": "❌ تم إلغاء الحجز",
                    "message": "تم إلغاء حجزك. إذا كان لديك أي أسئلة، يرجى الاتصال بفريق الدعم لدينا."
                }
            }
        }
    
    @staticmethod
    def get_payment_templates() -> Dict[str, Dict[str, str]]:
        """Templates for payment-related notifications"""
        return {
            NotificationType.PAYMENT_SUCCESS: {
                "en": {
                    "title": "✅ Payment Successful!",
                    "message": "Your payment has been processed successfully. Thank you for choosing our services!"
                },
                "ar": {
                    "title": "✅ تم الدفع بنجاح!",
                    "message": "تم معالجة دفعتك بنجاح. شكراً لاختيارك خدماتنا!"
                }
            },
            NotificationType.PAYMENT_FAILED: {
                "en": {
                    "title": "⚠️ Payment Failed",
                    "message": "Your payment could not be processed. Please check your payment details and try again."
                },
                "ar": {
                    "title": "⚠️ فشل في الدفع",
                    "message": "لم يتم معالجة دفعتك. يرجى التحقق من تفاصيل الدفع والمحاولة مرة أخرى."
                }
            }
        }
    
    @staticmethod
    def get_package_templates() -> Dict[str, Dict[str, str]]:
        """Templates for package-related notifications"""
        return {
            NotificationType.PACKAGE_UPDATE: {
                "en": {
                    "title": "📦 Package Update",
                    "message": "There's an update to one of your booked packages. Please check the details for any changes."
                },
                "ar": {
                    "title": "📦 تحديث الحزمة",
                    "message": "هناك تحديث على إحدى الحزم المحجوزة لديك. يرجى التحقق من التفاصيل لأي تغييرات."
                }
            }
        }
    
    @staticmethod
    def get_review_templates() -> Dict[str, Dict[str, str]]:
        """Templates for review-related notifications"""
        return {
            NotificationType.REVIEW_ADDED: {
                "en": {
                    "title": "⭐ New Review Added",
                    "message": "Thank you for your review! Your feedback helps us improve our services."
                },
                "ar": {
                    "title": "⭐ تم إضافة تقييم جديد",
                    "message": "شكراً لك على تقييمك! ملاحظاتك تساعدنا في تحسين خدماتنا."
                }
            }
        }
    
    @staticmethod
    def get_admin_templates() -> Dict[str, Dict[str, str]]:
        """Templates for admin announcements"""
        return {
            NotificationType.ADMIN_ANNOUNCEMENT: {
                "en": {
                    "title": "📢 Important Announcement",
                    "message": "We have an important announcement for all our valued customers."
                },
                "ar": {
                    "title": "📢 إعلان مهم",
                    "message": "لدينا إعلان مهم لجميع عملائنا الكرام."
                }
            }
        }
    
    @staticmethod
    def get_reminder_templates() -> Dict[str, Dict[str, str]]:
        """Templates for reminder notifications"""
        return {
            NotificationType.REMINDER: {
                "en": {
                    "title": "⏰ Reminder",
                    "message": "This is a friendly reminder about your upcoming travel plans."
                },
                "ar": {
                    "title": "⏰ تذكير",
                    "message": "هذا تذكير ودود حول خطط السفر القادمة لديك."
                }
            }
        }
    
    @staticmethod
    def get_promotion_templates() -> Dict[str, Dict[str, str]]:
        """Templates for promotional notifications"""
        return {
            NotificationType.PROMOTION: {
                "en": {
                    "title": "🎁 Special Offer!",
                    "message": "Don't miss out on our exclusive travel deals and special offers!"
                },
                "ar": {
                    "title": "🎁 عرض خاص!",
                    "message": "لا تفوت عروض السفر الحصرية والعروض الخاصة لدينا!"
                }
            }
        }
    
    @classmethod
    def get_all_templates(cls) -> Dict[str, Dict[str, Dict[str, str]]]:
        """Get all notification templates"""
        return {
            **cls.get_booking_templates(),
            **cls.get_payment_templates(),
            **cls.get_package_templates(),
            **cls.get_review_templates(),
            **cls.get_admin_templates(),
            **cls.get_reminder_templates(),
            **cls.get_promotion_templates()
        }
    
    @classmethod
    def get_template(cls, notification_type: NotificationType, language: str = "en") -> Dict[str, str]:
        """Get specific template for notification type and language"""
        all_templates = cls.get_all_templates()
        template = all_templates.get(notification_type, {})
        return template.get(language, template.get("en", {"title": "Notification", "message": "You have a new notification"}))
    
    @classmethod
    def format_template(cls, template: Dict[str, str], **kwargs) -> Dict[str, str]:
        """Format template with dynamic values"""
        formatted = {}
        for key, value in template.items():
            try:
                formatted[key] = value.format(**kwargs)
            except (KeyError, ValueError):
                formatted[key] = value
        return formatted

# Predefined notification templates for common scenarios
COMMON_TEMPLATES = {
    "welcome": {
        "en": {
            "title": "👋 Welcome to Dubai Travel Agency!",
            "message": "Welcome aboard! We're thrilled to have you as part of our travel family. Get ready for amazing adventures!"
        },
        "ar": {
            "title": "👋 مرحباً بك في وكالة دبي للسفر!",
            "message": "مرحباً بك على متن! نحن متحمسون لانضمامك إلى عائلة السفر لدينا. استعد للمغامرات المذهلة!"
        }
    },
    "booking_reminder_24h": {
        "en": {
            "title": "⏰ Travel Reminder - Tomorrow!",
            "message": "Your travel adventure starts tomorrow! Please ensure you have all necessary documents and arrive on time."
        },
        "ar": {
            "title": "⏰ تذكير السفر - غداً!",
            "message": "مغامرة السفر لديك تبدأ غداً! يرجى التأكد من وجود جميع المستندات اللازمة والوصول في الوقت المحدد."
        }
    },
    "booking_reminder_1h": {
        "en": {
            "title": "🚀 Final Reminder - Departure in 1 Hour!",
            "message": "Your departure is in 1 hour! Please make your way to the meeting point. Safe travels!"
        },
        "ar": {
            "title": "🚀 التذكير الأخير - المغادرة خلال ساعة!",
            "message": "مغادرتك خلال ساعة! يرجى التوجه إلى نقطة الالتقاء. رحلة سعيدة!"
        }
    },
    "weather_update": {
        "en": {
            "title": "🌤️ Weather Update",
            "message": "Weather conditions for your travel date have been updated. Please check the latest forecast."
        },
        "ar": {
            "title": "🌤️ تحديث الطقس",
            "message": "تم تحديث ظروف الطقس لتاريخ سفرك. يرجى التحقق من أحدث التوقعات."
        }
    },
    "cancellation_policy": {
        "en": {
            "title": "📋 Cancellation Policy Reminder",
            "message": "Please review our cancellation policy. Free cancellation is available up to 24 hours before departure."
        },
        "ar": {
            "title": "📋 تذكير سياسة الإلغاء",
            "message": "يرجى مراجعة سياسة الإلغاء لدينا. الإلغاء المجاني متاح حتى 24 ساعة قبل المغادرة."
        }
    }
}
