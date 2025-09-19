"""File upload service module.

Module provides file upload functionality using Cloudinary cloud storage.
Handles avatar image uploads with automatic resizing and optimization.

The module handles:
- Cloudinary configuration and authentication
- File upload to cloud storage
- Image transformation (resizing, cropping)
- URL generation for uploaded files
"""

import cloudinary
import cloudinary.uploader

from fastapi import UploadFile


class UploadFileService:
    """Service for uploading files to Cloudinary cloud storage."""

    def __init__(self, cloud_name, api_key, api_secret):
        """Initialize the upload service with Cloudinary credentials.

        Args:
            cloud_name: Cloudinary cloud name
            api_key: Cloudinary API key
            api_secret: Cloudinary API secret
        """
        self.cloud_name = cloud_name
        self.api_key = api_key
        self.api_secret = api_secret
        cloudinary.config(
            cloud_name=self.cloud_name,
            api_key=self.api_key,
            api_secret=self.api_secret,
            secure=True,
        )

    @staticmethod
    def upload_file(file: UploadFile, username: str) -> str:
        """Upload file to Cloudinary and return optimized URL.

        Args:
            file (UploadFile): File to upload (typically an image)
            username (str): Username for creating unique file path

        Returns:
            str: URL of the uploaded and transformed image
        """
        public_id = f"RestApp/{username}"
        r = cloudinary.uploader.upload(file.file, public_id=public_id, overwrite=True)
        src_url = cloudinary.CloudinaryImage(public_id).build_url(
            width=250, height=250, crop="fill", version=r.get("version")
        )
        return src_url
