"""
Storage provider abstraction — same rationale as the AI orchestrator: never
hard-couple business logic to one vendor's SDK. `resume/service.py` calls
`get_storage_client()` and only knows the `StorageClient` interface.
"""

import uuid
from abc import ABC, abstractmethod
from pathlib import Path

import httpx

from app.core.settings import settings


class StorageClient(ABC):
    @abstractmethod
    async def upload(self, *, file_bytes: bytes, filename: str, content_type: str) -> str:
        """Uploads a file and returns a publicly-fetchable URL."""
        raise NotImplementedError


class SupabaseStorageClient(StorageClient):
    def __init__(self):
        self.base_url = settings.SUPABASE_URL.rstrip("/")
        self.bucket = settings.SUPABASE_BUCKET
        self.service_key = settings.SUPABASE_SERVICE_KEY

    async def upload(self, *, file_bytes: bytes, filename: str, content_type: str) -> str:
        object_path = f"{uuid.uuid4()}-{filename}"
        upload_url = f"{self.base_url}/storage/v1/object/{self.bucket}/{object_path}"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                upload_url,
                content=file_bytes,
                headers={
                    "Authorization": f"Bearer {self.service_key}",
                    "Content-Type": content_type,
                    "x-upsert": "false",
                },
            )
            response.raise_for_status()

        return f"{self.base_url}/storage/v1/object/public/{self.bucket}/{object_path}"


class LocalDiskStorageClient(StorageClient):
    """Dev/test fallback — writes to LOCAL_STORAGE_DIR, served by main.py's
    static file mount at /local-files. Never used when SUPABASE_URL is set."""

    def __init__(self):
        self.root = Path(settings.LOCAL_STORAGE_DIR)
        self.root.mkdir(parents=True, exist_ok=True)

    async def upload(self, *, file_bytes: bytes, filename: str, content_type: str) -> str:
        object_name = f"{uuid.uuid4()}-{filename}"
        (self.root / object_name).write_bytes(file_bytes)
        return f"{settings.LOCAL_STORAGE_PUBLIC_BASE_URL}/{object_name}"


def get_storage_client() -> StorageClient:
    if settings.SUPABASE_URL and settings.SUPABASE_SERVICE_KEY:
        return SupabaseStorageClient()
    return LocalDiskStorageClient()
