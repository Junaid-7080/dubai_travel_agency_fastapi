# ===== notifications.py =====
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select
from typing import List, Optional
from datetime import datetime
import json

from database import get_session
from models import User, Notification, NotificationType, NotificationStatus
from schemas import (
    NotificationCreate, 
    NotificationResponse, 
    NotificationUpdate, 
    NotificationFilter,
    NotificationStats,
    BulkNotificationUpdate,
    APIResponse
)
from services.notification_service import NotificationService
from auth import get_current_user

router = APIRouter(prefix="/notifications", tags=["notifications"])

@router.get("/", response_model=List[NotificationResponse])
async def get_user_notifications(
    status: Optional[NotificationStatus] = Query(None),
    notification_type: Optional[NotificationType] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Get notifications for the current user"""
    notification_service = NotificationService(db)
    return await notification_service.get_user_notifications(
        user_id=current_user.id,
        status=status,
        notification_type=notification_type,
        page=page,
        size=size
    )

@router.get("/unread-count", response_model=dict)
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Get count of unread notifications"""
    notification_service = NotificationService(db)
    count = await notification_service.get_unread_count(current_user.id)
    return {"unread_count": count}

@router.get("/stats", response_model=NotificationStats)
async def get_notification_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Get notification statistics for the current user"""
    # Get total notifications
    total_query = select(Notification).where(Notification.user_id == current_user.id)
    total_notifications = len(db.exec(total_query).all())
    
    # Get unread count
    unread_query = select(Notification).where(
        Notification.user_id == current_user.id,
        Notification.status == NotificationStatus.UNREAD
    )
    unread_count = len(db.exec(unread_query).all())
    
    # Get read count
    read_query = select(Notification).where(
        Notification.user_id == current_user.id,
        Notification.status == NotificationStatus.READ
    )
    read_count = len(db.exec(read_query).all())
    
    # Get archived count
    archived_query = select(Notification).where(
        Notification.user_id == current_user.id,
        Notification.status == NotificationStatus.ARCHIVED
    )
    archived_count = len(db.exec(archived_query).all())
    
    # Get count by type
    by_type = {}
    for notification_type in NotificationType:
        type_query = select(Notification).where(
            Notification.user_id == current_user.id,
            Notification.notification_type == notification_type
        )
        by_type[notification_type.value] = len(db.exec(type_query).all())
    
    return NotificationStats(
        total_notifications=total_notifications,
        unread_count=unread_count,
        read_count=read_count,
        archived_count=archived_count,
        by_type=by_type
    )

@router.post("/", response_model=NotificationResponse)
async def create_notification(
    notification_data: NotificationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Create a new notification (admin only)"""
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create notifications"
        )
    
    notification_service = NotificationService(db)
    return await notification_service.create_notification(notification_data)

@router.post("/broadcast", response_model=NotificationResponse)
async def create_broadcast_notification(
    title_en: str,
    title_ar: str,
    message_en: str,
    message_ar: str,
    notification_type: NotificationType = NotificationType.ADMIN_ANNOUNCEMENT,
    priority: int = 2,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Create broadcast notification (admin only)"""
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create broadcast notifications"
        )
    
    notification_service = NotificationService(db)
    return await notification_service.create_broadcast_notification(
        title_en=title_en,
        title_ar=title_ar,
        message_en=message_en,
        message_ar=message_ar,
        notification_type=notification_type,
        priority=priority
    )

@router.put("/{notification_id}/read", response_model=APIResponse)
async def mark_notification_as_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Mark a notification as read"""
    notification_service = NotificationService(db)
    success = await notification_service.mark_as_read(notification_id, current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found or access denied"
        )
    
    return APIResponse(
        success=True,
        message="Notification marked as read"
    )

@router.put("/mark-all-read", response_model=APIResponse)
async def mark_all_notifications_as_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Mark all notifications as read for the current user"""
    notification_service = NotificationService(db)
    count = await notification_service.mark_all_as_read(current_user.id)
    
    return APIResponse(
        success=True,
        message=f"Marked {count} notifications as read"
    )

@router.put("/bulk-update", response_model=APIResponse)
async def bulk_update_notifications(
    update_data: BulkNotificationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Bulk update notification status"""
    updated_count = 0
    
    for notification_id in update_data.notification_ids:
        notification = db.get(Notification, notification_id)
        if notification and notification.user_id == current_user.id:
            notification.status = update_data.status
            if update_data.status == NotificationStatus.READ:
                notification.read_at = datetime.utcnow()
            updated_count += 1
    
    db.commit()
    
    return APIResponse(
        success=True,
        message=f"Updated {updated_count} notifications"
    )

@router.delete("/{notification_id}", response_model=APIResponse)
async def delete_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Delete a notification (mark as archived)"""
    notification = db.get(Notification, notification_id)
    if not notification or notification.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found or access denied"
        )
    
    notification.status = NotificationStatus.ARCHIVED
    db.commit()
    
    return APIResponse(
        success=True,
        message="Notification archived"
    )

@router.get("/admin/all", response_model=List[NotificationResponse])
async def get_all_notifications_admin(
    user_id: Optional[int] = Query(None),
    status: Optional[NotificationStatus] = Query(None),
    notification_type: Optional[NotificationType] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Get all notifications (admin only)"""
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view all notifications"
        )
    
    query = select(Notification)
    
    if user_id:
        query = query.where(Notification.user_id == user_id)
    if status:
        query = query.where(Notification.status == status)
    if notification_type:
        query = query.where(Notification.notification_type == notification_type)
    
    query = query.order_by(Notification.created_at.desc())
    query = query.offset((page - 1) * size).limit(size)
    
    notifications = db.exec(query).all()
    
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

@router.post("/send/{notification_id}", response_model=APIResponse)
async def send_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Send a notification (admin only)"""
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can send notifications"
        )
    
    notification_service = NotificationService(db)
    success = await notification_service.send_notification(notification_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found or failed to send"
        )
    
    return APIResponse(
        success=True,
        message="Notification sent successfully"
    )
