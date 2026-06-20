from functools import lru_cache

from app.core.config import get_settings
from app.storage.base import StorageClient
from app.storage.s3 import S3StorageClient, build_s3_client

__all__ = ["StorageClient", "get_storage_client"]


@lru_cache(maxsize=1)
def get_storage_client() -> StorageClient:
    settings = get_settings()
    storage = S3StorageClient(build_s3_client(settings), settings.s3_bucket)
    storage.ensure_bucket()
    return storage
