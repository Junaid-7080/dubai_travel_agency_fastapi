# ===== test_notifications.py =====
"""
Test script to demonstrate the notification system
Run this script to test the notification functionality
"""

import asyncio
from sqlmodel import Session, create_engine, SQLModel
from database import get_db
from services.notification_helper import NotificationHelper
from services.notification_service import NotificationService
from models import User, Booking, Package, NotificationType
from datetime import datetime, timedelta

# Test database setup (you may need to adjust this)
SQLALCHEMY_DATABASE_URL = "sqlite:///./dubai_travel.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)

def create_tables():
    """Create database tables"""
    SQLModel.metadata.create_all(engine)

async def test_notification_system():
    """Test the notification system"""
    print("🚀 Testing Notification System...")
    
    # Create tables
    create_tables()
    
    # Create test session
    with Session(engine) as db:
        # Create test user
        test_user = User(
            name="Test User",
            email="test@example.com",
            password_hash="hashed_password",
            language="en",
            role="customer"
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        print(f"✅ Created test user: {test_user.name}")
        
        # Create test package
        test_package = Package(
            title_en="Dubai City Tour",
            title_ar="جولة دبي السياحية",
            description_en="Explore the beautiful city of Dubai",
            description_ar="استكشف مدينة دبي الجميلة",
            price=150.0,
            duration="4 hours",
            max_travelers=20
        )
        db.add(test_package)
        db.commit()
        db.refresh(test_package)
        print(f"✅ Created test package: {test_package.title_en}")
        
        # Create test booking
        test_booking = Booking(
            user_id=test_user.id,
            package_id=test_package.id,
            travel_date=datetime.now() + timedelta(days=7),
            travelers_count=2,
            total_price=300.0,
            status="confirmed",
            booking_reference="TEST001"
        )
        db.add(test_booking)
        db.commit()
        db.refresh(test_booking)
        print(f"✅ Created test booking: {test_booking.booking_reference}")
        
        # Initialize notification helper
        notification_helper = NotificationHelper(db)
        
        # Test 1: Send welcome notification
        print("\n📧 Testing welcome notification...")
        welcome_result = await notification_helper.send_welcome_notification(test_user)
        print(f"Welcome notification: {'✅ Sent' if welcome_result else '❌ Failed'}")
        
        # Test 2: Send booking confirmation
        print("\n📧 Testing booking confirmation...")
        booking_result = await notification_helper.send_booking_confirmation(test_booking)
        print(f"Booking confirmation: {'✅ Sent' if booking_result else '❌ Failed'}")
        
        # Test 3: Send travel reminder
        print("\n📧 Testing travel reminder...")
        reminder_result = await notification_helper.send_travel_reminder(test_booking, hours_before=24)
        print(f"Travel reminder: {'✅ Sent' if reminder_result else '❌ Failed'}")
        
        # Test 4: Send broadcast announcement
        print("\n📧 Testing broadcast announcement...")
        broadcast_result = await notification_helper.send_broadcast_announcement(
            title_en="System Maintenance",
            title_ar="صيانة النظام",
            message_en="We will be performing system maintenance tonight.",
            message_ar="سنقوم بصيانة النظام الليلة."
        )
        print(f"Broadcast announcement: {'✅ Sent' if broadcast_result else '❌ Failed'}")
        
        # Test 5: Get user notifications
        print("\n📱 Testing notification retrieval...")
        notification_service = NotificationService(db)
        user_notifications = await notification_service.get_user_notifications(test_user.id)
        print(f"User notifications count: {len(user_notifications)}")
        
        # Test 6: Get unread count
        unread_count = await notification_service.get_unread_count(test_user.id)
        print(f"Unread notifications: {unread_count}")
        
        # Test 7: Mark as read
        if user_notifications:
            first_notification = user_notifications[0]
            mark_result = await notification_service.mark_as_read(first_notification.id, test_user.id)
            print(f"Mark as read: {'✅ Success' if mark_result else '❌ Failed'}")
        
        # Test 8: Get updated unread count
        updated_unread_count = await notification_service.get_unread_count(test_user.id)
        print(f"Updated unread count: {updated_unread_count}")
        
        print("\n🎉 Notification system test completed!")
        print(f"📊 Summary:")
        print(f"   - User: {test_user.name}")
        print(f"   - Total notifications: {len(user_notifications)}")
        print(f"   - Unread notifications: {updated_unread_count}")
        print(f"   - Welcome notification: {'✅' if welcome_result else '❌'}")
        print(f"   - Booking confirmation: {'✅' if booking_result else '❌'}")
        print(f"   - Travel reminder: {'✅' if reminder_result else '❌'}")
        print(f"   - Broadcast announcement: {'✅' if broadcast_result else '❌'}")

if __name__ == "__main__":
    print("🔔 Dubai Travel Agency - Notification System Test")
    print("=" * 50)
    asyncio.run(test_notification_system())
