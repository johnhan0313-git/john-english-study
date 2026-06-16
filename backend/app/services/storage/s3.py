from __future__ import annotations

import logging

import boto3
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)


class S3StorageBackend:
    def __init__(self, settings: Settings | None = None) -> None:
        cfg = settings or get_settings()
        self._bucket = cfg.s3_bucket
        self._client = boto3.client(
            "s3",
            endpoint_url=cfg.s3_endpoint_url or None,
            aws_access_key_id=cfg.s3_access_key,
            aws_secret_access_key=cfg.s3_secret_key,
            region_name=cfg.s3_region,
            use_ssl=cfg.s3_use_ssl,
            config=BotoConfig(
                s3={"addressing_style": "path"},
                connect_timeout=5,
                read_timeout=30,
                retries={"max_attempts": 3},
            ),
        )
        self._ensure_bucket()

    def _ensure_bucket(self) -> None:
        try:
            self._client.head_bucket(Bucket=self._bucket)
        except ClientError:
            self._client.create_bucket(Bucket=self._bucket)
            logger.info("Created S3 bucket %s", self._bucket)

    def _normalize_key(self, key: str) -> str:
        return key.lstrip("/").replace("\\", "/")

    def exists(self, key: str) -> bool:
        normalized = self._normalize_key(key)
        try:
            self._client.head_object(Bucket=self._bucket, Key=normalized)
            return True
        except ClientError as exc:
            code = exc.response.get("Error", {}).get("Code", "")
            if code in ("404", "NoSuchKey", "NotFound"):
                return False
            raise

    def get_bytes(self, key: str) -> bytes:
        normalized = self._normalize_key(key)
        response = self._client.get_object(Bucket=self._bucket, Key=normalized)
        return response["Body"].read()

    def put_bytes(self, key: str, data: bytes, content_type: str) -> None:
        normalized = self._normalize_key(key)
        self._client.put_object(
            Bucket=self._bucket,
            Key=normalized,
            Body=data,
            ContentType=content_type,
        )

    def delete(self, key: str) -> None:
        normalized = self._normalize_key(key)
        self._client.delete_object(Bucket=self._bucket, Key=normalized)

    def clear_bucket(self) -> None:
        paginator = self._client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self._bucket):
            contents = page.get("Contents", [])
            if not contents:
                continue
            self._client.delete_objects(
                Bucket=self._bucket,
                Delete={"Objects": [{"Key": obj["Key"]} for obj in contents]},
            )
