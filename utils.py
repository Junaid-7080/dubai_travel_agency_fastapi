# ===== utils.py =====
import os
import uuid
from typing import List, Optional
from fastapi import UploadFile, HTTPException, status
from PIL import Image
import json
from config import settings

def save_uploaded_file(file: UploadFile, subfolder: str = "packages") -> str:
    """Save uploaded file and return file path"""
    if file.size > settings.max_file_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large"
        )
    
    # Generate unique filename
    file_extension = file.filename.split(".")[-1] if file.filename else "jpg"
    filename = f"{uuid.uuid4()}.{file_extension}"
    
    # Create subfolder if it doesn't exist
    folder_path = os.path.join(settings.upload_dir, subfolder)
    os.makedirs(folder_path, exist_ok=True)
    
    file_path = os.path.join(folder_path, filename)
    
    # Save file
    with open(file_path, "wb") as buffer:
        content = file.file.read()
        buffer.write(content)
    
    # If it's an image, create thumbnail
    if file_extension.lower() in ['jpg', 'jpeg', 'png', 'webp']:
        create_thumbnail(file_path)
    
    return f"/{file_path}"

def create_thumbnail(image_path: str, size: tuple = (300, 200)):
    """Create thumbnail for image"""
    try:
        with Image.open(image_path) as img:
            img.thumbnail(size, Image.Resampling.LANCZOS)
            
            # Save thumbnail with _thumb suffix
            path_parts = image_path.rsplit('.', 1)
            thumb_path = f"{path_parts[0]}_thumb.{path_parts[1]}"
            img.save(thumb_path, optimize=True, quality=85)
    except Exception:
        pass  # Ignore thumbnail creation errors

def serialize_images(images: Optional[List[str]]) -> Optional[str]:
    """Convert image list to JSON string for database storage"""
    return json.dumps(images) if images else None

def deserialize_images(images_json: Optional[str]) -> Optional[List[str]]:
    """Convert JSON string to image list"""
    try:
        return json.loads(images_json) if images_json else None
    except json.JSONDecodeError:
        return None

def get_localized_content(content_en: str, content_ar: str, language: str) -> str:
    """Get content in requested language"""
    return content_ar if language == "ar" else content_en

def validate_travel_date(travel_date: str) -> bool:
    """Validate that travel date is in the future"""
    from datetime import datetime
    try:
        date_obj = datetime.fromisoformat(travel_date.replace('Z', '+00:00'))
        return date_obj > datetime.utcnow()
    except ValueError:
        return False