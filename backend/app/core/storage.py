"""Object storage abstraction.

Two backends are supported:

* ``local`` — a filesystem tree under ``STORAGE_LOCAL_ROOT`` (default for development)
* ``s3``    — any S3-compatible object store via boto3 (MinIO locally, cloud in prod)

The abstraction exposes a small surface so the rest of the application never
cares where bytes actually live.
"""

from __future__ import annotations

import io
import os
import uuid
from abc import ABC, abstractmethod
from pathlib import Path

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from app.core.config import settings


class StorageError(Exception):
    pass


class StorageBackend(ABC):
    @abstractmethod
    def put(self, key: str, data: bytes, content_type: str | None = None) -> str: ...

    @abstractmethod
    def get(self, key: str) -> bytes: ...

    @abstractmethod
    def exists(self, key: str) -> bool: ...

    @abstractmethod
    def delete(self, key: str) -> None: ...

    @abstractmethod
    def public_url(self, key: str) -> str | None: ...


class LocalStorage(StorageBackend):
    """Filesystem-backed storage for local development and tests."""

    def __init__(self, root: str = "./data") -> None:
        self.root = Path(root)

    def _path(self, key: str) -> Path:
        # Prevent path traversal.
        safe = Path(key)
        if ".." in safe.parts:
            raise StorageError("invalid key")
        return self.root / safe

    def put(self, key: str, data: bytes, content_type: str | None = None) -> str:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return key

    def get(self, key: str) -> bytes:
        path = self._path(key)
        if not path.exists():
            raise StorageError(f"object not found: {key}")
        return path.read_bytes()

    def exists(self, key: str) -> bool:
        return self._path(key).exists()

    def delete(self, key: str) -> None:
        path = self._path(key)
        if path.exists():
            path.unlink()

    def public_url(self, key: str) -> str | None:
        return None


class S3Storage(StorageBackend):
    """S3-compatible storage via boto3 (MinIO, AWS S3, etc.)."""

    def __init__(
        self,
        endpoint: str | None,
        access_key: str,
        secret_key: str,
        bucket: str,
        region: str = "us-east-1",
        public_base_url: str | None = None,
    ) -> None:
        self.bucket = bucket
        self.public_base_url = public_base_url
        kwargs: dict = {"region_name": region}
        if endpoint:
            kwargs.update(
                {
                    "endpoint_url": endpoint,
                    "aws_access_key_id": access_key,
                    "aws_secret_access_key": secret_key,
                    "config": Config(signature_version="s3v4"),
                }
            )
        self.client = boto3.client("s3", **kwargs)
        self._ensure_bucket()

    def _ensure_bucket(self) -> None:
        try:
            self.client.head_bucket(Bucket=self.bucket)
        except ClientError:
            self.client.create_bucket(Bucket=self.bucket)

    def put(self, key: str, data: bytes, content_type: str | None = None) -> str:
        extra = {"ContentType": content_type} if content_type else {}
        self.client.put_object(Bucket=self.bucket, Key=key, Body=data, **extra)
        return key

    def get(self, key: str) -> bytes:
        try:
            resp = self.client.get_object(Bucket=self.bucket, Key=key)
            return resp["Body"].read()
        except ClientError as exc:
            raise StorageError(f"object not found: {key}") from exc

    def exists(self, key: str) -> bool:
        try:
            self.client.head_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError:
            return False

    def delete(self, key: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=key)

    def public_url(self, key: str) -> str | None:
        if self.public_base_url:
            return f"{self.public_base_url.rstrip('/')}/{key}"
        return None


def get_storage() -> StorageBackend:
    if settings.storage_backend == "s3":
        return S3Storage(
            endpoint=settings.storage_endpoint,
            access_key=settings.storage_access_key or "",
            secret_key=settings.storage_secret_key or "",
            bucket=settings.storage_bucket,
            region=settings.storage_region,
            public_base_url=settings.storage_public_base_url,
        )
    return LocalStorage(root=settings.storage_local_root)


def build_object_key(object_code: str, kind: str, filename: str) -> str:
    """Storage layout:

    originals/MZ-UG-LGD-STORY-00000001/<uuid>-<filename>
    derivatives/MZ-UG-LGD-STORY-00000001/<uuid>-<filename>
    """
    safe_name = os.path.basename(filename).replace(" ", "_")
    unique = uuid.uuid4().hex[:8]
    return f"{kind}/{object_code}/{unique}-{safe_name}"