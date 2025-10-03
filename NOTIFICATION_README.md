# 🔔 Notification System Documentation

## Overview
This notification system provides comprehensive notification functionality for the Dubai Travel Agency FastAPI application. It supports multiple notification types, bilingual content (English/Arabic), and various delivery methods.

## Features

### 📱 Notification Types
- **Booking Notifications**: Confirmation, cancellation, updates
- **Payment Notifications**: Success, failure, refunds
- **Package Updates**: Changes to booked packages
- **Review Notifications**: New reviews and ratings
- **Admin Announcements**: Broadcast messages to all users
- **Reminders**: Travel reminders and important updates
- **Promotions**: Special offers and deals

### 🌍 Bilingual Support
- Full English and Arabic support
- Automatic language detection based on user preferences
- Localized templates and messages

### 📊 Notification Management
- Mark as read/unread
- Bulk operations
- Notification statistics
- Archive functionality
- Priority levels (1-4: Low, Medium, High, Urgent)

## API Endpoints

### User Endpoints
```
GET /notifications/ - Get user notifications
GET /notifications/unread-count - Get unread count
GET /notifications/stats - Get notification statistics
PUT /notifications/{id}/read - Mark notification as read
PUT /notifications/mark-all-read - Mark all as read
PUT /notifications/bulk-update - Bulk update notifications
DELETE /notifications/{id} - Archive notification
```

### Admin Endpoints
```
POST /notifications/ - Create notification (admin only)
POST /notifications/broadcast - Create broadcast notification
GET /notifications/admin/all - Get all notifications
POST /notifications/send/{id} - Send notification
```

## Usage Examples

### 1. Creating a Notification
```python
from services.notification_service import NotificationService

notification_service = NotificationService(db)
notification = await notification_service.create_notification({
    "title_en": "Booking Confirmed!",
    "title_ar": "تم تأكيد الحجز!",
    "message_en": "Your booking has been confirmed.",
    "message_ar": "تم تأكيد حجزك.",
    "notification_type": "booking_confirmed",
    "user_id": user_id,
    "priority": 3
})
```

### 2. Sending Booking Confirmation
```python
from services.notification_helper import NotificationHelper

notification_helper = NotificationHelper(db)
await notification_helper.send_booking_confirmation(booking)
```

### 3. Sending Payment Success
```python
await notification_helper.send_payment_success(payment)
```

### 4. Sending Travel Reminder
```python
await notification_helper.send_travel_reminder(booking, hours_before=24)
```

### 5. Sending Broadcast Announcement
```python
await notification_helper.send_broadcast_announcement(
    title_en="Important Update",
    title_ar="تحديث مهم",
    message_en="We have an important announcement.",
    message_ar="لدينا إعلان مهم."
)
```

## Integration with Existing Endpoints

### Booking Confirmation
```python
# In your booking confirmation endpoint
async def confirm_booking(booking_id: int, db: Session = Depends(get_db)):
    booking = db.get(Booking, booking_id)
    booking.status = "confirmed"
    db.commit()
    
    # Send notification
    notification_helper = NotificationHelper(db)
    await notification_helper.send_booking_confirmation(booking)
    
    return {"message": "Booking confirmed"}
```

### Payment Processing
```python
# In your payment success endpoint
async def process_payment(payment_id: int, db: Session = Depends(get_db)):
    payment = db.get(Payment, payment_id)
    payment.status = "paid"
    db.commit()
    
    # Send notification
    notification_helper = NotificationHelper(db)
    await notification_helper.send_payment_success(payment)
    
    return {"message": "Payment processed"}
```

## Database Schema

### Notification Model
```python
class Notification(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    title_en: str
    title_ar: str
    message_en: str
    message_ar: str
    notification_type: NotificationType
    priority: int = 1
    user_id: Optional[int] = None  # None for broadcast
    status: NotificationStatus = "unread"
    sent_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    created_at: datetime
    data: Optional[str] = None  # JSON data
```

## Notification Types

### Booking Notifications
- `booking_confirmed` - Booking confirmed successfully
- `booking_cancelled` - Booking cancelled
- `booking_updated` - Booking details updated

### Payment Notifications
- `payment_success` - Payment processed successfully
- `payment_failed` - Payment failed
- `payment_refunded` - Payment refunded

### System Notifications
- `package_update` - Package information updated
- `review_added` - New review added
- `admin_announcement` - Admin broadcast
- `reminder` - Travel reminders
- `promotion` - Promotional offers

## Priority Levels
- **1 (Low)**: General information
- **2 (Medium)**: Important updates
- **3 (High)**: Urgent notifications
- **4 (Urgent)**: Critical alerts

## Templates

The system includes pre-built templates for common scenarios:

### Welcome Template
```python
welcome = {
    "en": {
        "title": "👋 Welcome to Dubai Travel Agency!",
        "message": "Welcome aboard! We're thrilled to have you as part of our travel family."
    },
    "ar": {
        "title": "👋 مرحباً بك في وكالة دبي للسفر!",
        "message": "مرحباً بك على متن! نحن متحمسون لانضمامك إلى عائلة السفر لدينا."
    }
}
```

### Travel Reminder Template
```python
booking_reminder_24h = {
    "en": {
        "title": "⏰ Travel Reminder - Tomorrow!",
        "message": "Your travel adventure starts tomorrow! Please ensure you have all necessary documents."
    },
    "ar": {
        "title": "⏰ تذكير السفر - غداً!",
        "message": "مغامرة السفر لديك تبدأ غداً! يرجى التأكد من وجود جميع المستندات اللازمة."
    }
}
```

## Scheduled Tasks

### Travel Reminders
Set up a scheduled task to send travel reminders:

```python
# Run every hour
async def send_travel_reminders():
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
```

## Frontend Integration

### Get User Notifications
```javascript
// Fetch user notifications
const response = await fetch('/notifications/', {
    headers: {
        'Authorization': `Bearer ${token}`
    }
});
const notifications = await response.json();
```

### Mark as Read
```javascript
// Mark notification as read
await fetch(`/notifications/${notificationId}/read`, {
    method: 'PUT',
    headers: {
        'Authorization': `Bearer ${token}`
    }
});
```

### Get Unread Count
```javascript
// Get unread count for badge
const response = await fetch('/notifications/unread-count', {
    headers: {
        'Authorization': `Bearer ${token}`
    }
});
const { unread_count } = await response.json();
```

## Configuration

### Email Settings
Configure email settings in your environment variables:
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-password
```

### SMS Settings
Configure SMS settings for Twilio:
```env
TWILIO_ACCOUNT_SID=your-account-sid
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_PHONE_NUMBER=your-phone-number
```

## Testing

### Test Notification Creation
```python
# Test creating a notification
async def test_notification():
    notification_helper = NotificationHelper(db)
    
    # Create test booking
    booking = Booking(...)
    
    # Send notification
    result = await notification_helper.send_booking_confirmation(booking)
    assert result == True
```

## Error Handling

The notification system includes comprehensive error handling:
- Database connection errors
- Email/SMS delivery failures
- Template formatting errors
- User not found errors

## Performance Considerations

- Notifications are created asynchronously
- Database queries are optimized with proper indexing
- Bulk operations for better performance
- Rate limiting for external services

## Security

- User authentication required for all endpoints
- Admin-only endpoints for sensitive operations
- Input validation and sanitization
- SQL injection protection

## Monitoring

- Notification delivery status tracking
- Error logging and monitoring
- Performance metrics
- User engagement analytics

## Future Enhancements

- Push notifications for mobile apps
- WebSocket support for real-time notifications
- Advanced filtering and search
- Notification preferences per user
- A/B testing for notification content
- Analytics dashboard for notification performance
