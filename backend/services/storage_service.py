"""
Supabase Storage via direct REST API.
NO supabase-py client - pure HTTP requests.
"""
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class SupabaseStorageService:
    """
    Direct REST API wrapper for Supabase Storage.
    Easily swappable - just implement the same interface.
    """

    def __init__(self):
        self.base_url = settings.SUPABASE_URL
        self.api_key = settings.SUPABASE_SERVICE_KEY
        self.headers = {
            'apikey': self.api_key,
            'Authorization': f'Bearer {self.api_key}',
        }

    def upload(self, bucket: str, path: str, file_content: bytes, content_type: str) -> dict:
        """Upload a file to a Supabase Storage bucket."""
        url = f'{self.base_url}/storage/v1/object/{bucket}/{path}'
        headers = {**self.headers, 'Content-Type': content_type}
        response = requests.post(url, headers=headers, data=file_content, timeout=60)
        response.raise_for_status()
        logger.info('Uploaded %s to bucket %s', path, bucket)
        return {'path': path, 'bucket': bucket}

    def upload_update(self, bucket: str, path: str, file_content: bytes, content_type: str) -> dict:
        """Update (PUT) an existing file in Supabase Storage."""
        url = f'{self.base_url}/storage/v1/object/{bucket}/{path}'
        headers = {**self.headers, 'Content-Type': content_type}
        response = requests.put(url, headers=headers, data=file_content, timeout=60)
        response.raise_for_status()
        return {'path': path, 'bucket': bucket}

    def get_public_url(self, bucket: str, path: str) -> str:
        """Get the public URL for a file (bucket must be public)."""
        return f'{self.base_url}/storage/v1/object/public/{bucket}/{path}'

    def get_signed_url(self, bucket: str, path: str, expires_in: int = 3600) -> str:
        """Get a signed URL for a private file."""
        url = f'{self.base_url}/storage/v1/object/sign/{bucket}/{path}'
        response = requests.post(
            url,
            headers={**self.headers, 'Content-Type': 'application/json'},
            json={'expiresIn': expires_in},
            timeout=30,
        )
        response.raise_for_status()
        signed_url = response.json().get('signedURL', '')
        return f'{self.base_url}{signed_url}'

    def delete(self, bucket: str, paths: list) -> bool:
        """Delete one or more files from a bucket."""
        url = f'{self.base_url}/storage/v1/object/{bucket}'
        response = requests.delete(
            url,
            headers={**self.headers, 'Content-Type': 'application/json'},
            json={'prefixes': paths},
            timeout=30,
        )
        if response.status_code == 200:
            logger.info('Deleted %d files from bucket %s', len(paths), bucket)
            return True
        logger.warning('Delete failed (status %d): %s', response.status_code, response.text)
        return False

    def list_files(self, bucket: str, prefix: str = '', limit: int = 100) -> list:
        """List files in a bucket with optional prefix."""
        url = f'{self.base_url}/storage/v1/object/list/{bucket}'
        response = requests.post(
            url,
            headers={**self.headers, 'Content-Type': 'application/json'},
            json={'prefix': prefix, 'limit': limit, 'sortBy': {'column': 'name', 'order': 'asc'}},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def create_bucket_if_not_exists(self, bucket: str, public: bool = False) -> None:
        """Create a storage bucket if it doesn't already exist."""
        url = f'{self.base_url}/storage/v1/bucket'
        response = requests.post(
            url,
            headers={**self.headers, 'Content-Type': 'application/json'},
            json={'id': bucket, 'name': bucket, 'public': public},
            timeout=30,
        )
        # 409 = already exists, that's OK
        if response.status_code not in [200, 201, 409]:
            logger.error('Failed to create bucket %s: %s', bucket, response.text)
            response.raise_for_status()
        elif response.status_code in [200, 201]:
            logger.info('Bucket created: %s (public=%s)', bucket, public)


storage_service = SupabaseStorageService()
