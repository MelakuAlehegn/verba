from __future__ import annotations

from typing import Protocol


class StorageClient(Protocol):
    """Object-storage contract the rest of the app depends on.

    A Protocol (structural typing): any class with these methods satisfies it,
    so swapping S3/MinIO for another backend needs no change at call sites.
    """

    def put_object(self, key: str, data: bytes, content_type: str) -> None: ...

    def get_object(self, key: str) -> bytes: ...

    def delete_object(self, key: str) -> None: ...

    def generate_presigned_url(self, key: str, *, expires_in: int = 3600) -> str: ...
