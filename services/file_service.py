# ===== services/file_service.py =====
import os
import uuid
import aiofiles
from fastapi import UploadFile, HTTPException, status
from PIL import Image
import io
from typing import List, Optional
from config import settings

class FileService:
    def __init__(self):
        self.upload_dir = settings.upload_dir
        self.max_file_size = settings.max_file_size
        self.allowed_extensions = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
    
    def _is_allowed_file(self, filename: str) -> bool:
        """Check if file extension is allowed"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.allowed_extensions
    
    async def save_upload_file(self, file: UploadFile, subfolder: str = "general") -> str:
        """Save uploaded file and return path"""
        if not self._is_allowed_file(file.filename):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File type not allowed"
            )
        
        # Check file size
        file_size = 0
        content = await file.read()
        file_size = len(content)
        
        if file_size > self.max_file_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds {self.max_file_size} bytes"
            )
        
        # Generate unique filename
        file_extension = file.filename.split('.')[-1].lower()
        filename = f"{uuid.uuid4()}.{file_extension}"
        
        # Create directory if it doesn't exist
        folder_path = os.path.join(self.upload_dir, subfolder)
        os.makedirs(folder_path, exist_ok=True)
        
        file_path = os.path.join(folder_path, filename)
        
        # Save file
        async with aiofiles.open(file_path, 'wb') as buffer:
            await buffer.write(content)
        
        # Create thumbnail for images
        if file_extension in ['jpg', 'jpeg', 'png', 'webp']:
            await self._create_thumbnail(file_path, content)
        
        return f"/{file_path}"
    
    async def _create_thumbnail(self, file_path: str, content: bytes):
        """Create thumbnail for image"""
        try:
            # Open image from bytes
            image = Image.open(io.BytesIO(content))
            
            # Create thumbnail
            thumbnail_size = (300, 200)
            image.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)
            
            # Save thumbnail
            path_parts = file_path.rsplit('.', 1)
            thumb_path = f"{path_parts[0]}_thumb.{path_parts[1]}"
            image.save(thumb_path, optimize=True, quality=85)
            
        except Exception as e:
            # Log error but don't fail the upload
            print(f"Thumbnail creation failed: {e}")
    
    def delete_file(self, file_path: str) -> bool:
        """Delete file from storage"""
        try:
            # Remove leading slash if present
            if file_path.startswith('/'):
                file_path = file_path[1:]
            
            full_path = os.path.join(self.upload_dir, file_path)
            
            if os.path.exists(full_path):
                os.remove(full_path)
                
                # Also delete thumbnail if exists
                path_parts = full_path.rsplit('.', 1)
                thumb_path = f"{path_parts[0]}_thumb.{path_parts[1]}"
                if os.path.exists(thumb_path):
                    os.remove(thumb_path)
                
                return True
            return False
        except Exception:
            return False

file_service = FileService()
