# ===== services/notification_service.py =====
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from twilio.rest import Client
from jinja2 import Environment, FileSystemLoader
from typing import Dict, Any
import os
from config import settings
import logging

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self):
        self.smtp_server = settings.smtp_server
        self.smtp_port = settings.smtp_port
        self.smtp_username = settings.smtp_username
        self.smtp_password = settings.smtp_password
        
        # Initialize Twilio client
        try:
            self.twilio_client = Client(
                settings.twilio_account_sid,
                settings.twilio_auth_token
            )
        except Exception as e:
            logger.warning(f"Failed to initialize Twilio client: {e}")
            self.twilio_client = None
        
        # Initialize Jinja2 environment for email templates
        template_dir = os.path.join(os.path.dirname(__file__), '..', 'templates')
        self.jinja_env = Environment(loader=FileSystemLoader(template_dir))

    async def send_email(self, to_email: str, subject: str, template_name: str, context: Dict[str, Any]):
        """Send email using SMTP"""
        try:
            # Load and render template
            template = self.jinja_env.get_template(f"{template_name}.html")
            html_body = template.render(**context)
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.smtp_username
            msg['To'] = to_email
            
            # Add HTML part
            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    async def send_sms(self, to_phone: str, message: str):
        """Send SMS using Twilio"""
        if not self.twilio_client:
            logger.warning("Twilio client not initialized")
            return False
        
        try:
            # Ensure phone number has country code
            if not to_phone.startswith('+'):
                to_phone = f"+971{to_phone}"  # UAE country code
            
            message = self.twilio_client.messages.create(
                body=message,
                from_=settings.twilio_phone_number,
                to=to_phone
            )
            
            logger.info(f"SMS sent successfully to {to_phone}, SID: {message.sid}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send SMS to {to_phone}: {e}")
            return False

    async def send_booking_confirmation(self, booking_data: Dict[str, Any], language: str = "en"):
        """Send booking confirmation email and SMS"""
        email_subject = "Booking Confirmation - Dubai Travel Agency"
        if language == "ar":
            email_subject = "تأكيد الحجز - وكالة دبي للسفر"
        
        template_name = f"booking_confirmation_{language}"
        
        # Send email
        email_sent = await self.send_email(
            booking_data['user_email'],
            email_subject,
            template_name,
            booking_data
        )
        
        # Send SMS if mobile number is available
        sms_sent = False
        if booking_data.get('user_mobile'):
            sms_message = f"Booking confirmed! Reference: {booking_data['booking_reference']}. Thank you for choosing Dubai Travel Agency."
            if language == "ar":
                sms_message = f"تم تأكيد الحجز! المرجع: {booking_data['booking_reference']}. شكراً لاختيارك وكالة دبي للسفر."
            
            sms_sent = await self.send_sms(booking_data['user_mobile'], sms_message)
        
        return {"email_sent": email_sent, "sms_sent": sms_sent}

    async def send_otp(self, identifier: str, otp_code: str, method: str = "email"):
        """Send OTP via email or SMS"""
        if method == "email":
            subject = "Your OTP Code - Dubai Travel Agency"
            context = {"otp_code": otp_code}
            return await self.send_email(identifier, subject, "otp_email", context)
        
        elif method == "sms":
            message = f"Your OTP code is: {otp_code}. Valid for 5 minutes."
            return await self.send_sms(identifier, message)
        
        return False

# Initialize notification service
notification_service = NotificationService()