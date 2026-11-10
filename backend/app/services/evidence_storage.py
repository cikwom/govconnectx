import os
import socket
import struct

import boto3
from botocore.exceptions import BotoCoreError, ClientError


class StorageNotConfigured(RuntimeError):
    pass


def s3_is_configured() -> bool:
    return bool(
        os.getenv("OBJECT_STORAGE_BUCKET")
        and os.getenv("OBJECT_STORAGE_ACCESS_KEY_ID")
        and os.getenv("OBJECT_STORAGE_SECRET_ACCESS_KEY")
    )


def malware_scanner_is_configured() -> bool:
    return bool(os.getenv("CLAMAV_HOST"))


def _s3_client():
    if not s3_is_configured():
        raise StorageNotConfigured("Private object storage is not configured")
    return boto3.client(
        "s3",
        endpoint_url=os.getenv("OBJECT_STORAGE_ENDPOINT_URL") or None,
        region_name=os.getenv("OBJECT_STORAGE_REGION", "auto"),
        aws_access_key_id=os.getenv("OBJECT_STORAGE_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("OBJECT_STORAGE_SECRET_ACCESS_KEY"),
    )


def scan_bytes(data: bytes) -> None:
    """Require a clean ClamAV INSTREAM response when a scanner is configured."""
    host = os.getenv("CLAMAV_HOST")
    if not host:
        if os.getenv("ENVIRONMENT", "development").strip().lower() == "production":
            raise StorageNotConfigured("Malware scanning is required before production evidence uploads")
        return
    port = int(os.getenv("CLAMAV_PORT", "3310"))
    timeout = float(os.getenv("CLAMAV_TIMEOUT_SECONDS", "10"))
    try:
        with socket.create_connection((host, port), timeout=timeout) as connection:
            connection.settimeout(timeout)
            connection.sendall(b"zINSTREAM\0")
            view = memoryview(data)
            for offset in range(0, len(view), 64 * 1024):
                chunk = view[offset:offset + 64 * 1024]
                connection.sendall(struct.pack("!I", len(chunk)))
                connection.sendall(chunk)
            connection.sendall(struct.pack("!I", 0))
            response = b""
            while not response.endswith(b"\0") and len(response) < 4096:
                chunk = connection.recv(1024)
                if not chunk:
                    break
                response += chunk
    except OSError as exc:
        raise StorageNotConfigured("Malware scanning service is unavailable") from exc
    result = response.decode("utf-8", errors="replace").strip("\0 ")
    if not result.endswith("OK"):
        raise ValueError("The uploaded evidence did not pass malware scanning")


def store_object(storage_key: str, data: bytes, content_type: str, sha256: str) -> None:
    try:
        options = {}
        encryption = os.getenv("OBJECT_STORAGE_SERVER_SIDE_ENCRYPTION", "").strip()
        if encryption:
            options["ServerSideEncryption"] = encryption
        _s3_client().put_object(
            Bucket=os.environ["OBJECT_STORAGE_BUCKET"],
            Key=f"report-evidence/{storage_key}",
            Body=data,
            ContentLength=len(data),
            ContentType=content_type,
            Metadata={"sha256": sha256},
            **options,
        )
    except (BotoCoreError, ClientError) as exc:
        raise StorageNotConfigured("Could not store evidence in private object storage") from exc


def read_object(storage_key: str):
    try:
        return _s3_client().get_object(
            Bucket=os.environ["OBJECT_STORAGE_BUCKET"],
            Key=f"report-evidence/{storage_key}",
        )
    except (BotoCoreError, ClientError) as exc:
        raise FileNotFoundError("Evidence object is unavailable") from exc


def delete_object(storage_key: str) -> None:
    if not s3_is_configured():
        return
    try:
        _s3_client().delete_object(
            Bucket=os.environ["OBJECT_STORAGE_BUCKET"],
            Key=f"report-evidence/{storage_key}",
        )
    except (BotoCoreError, ClientError):
        # Preserve the original database/storage exception; operational cleanup can retry.
        pass


def storage_is_production_ready() -> bool:
    return s3_is_configured() and malware_scanner_is_configured()
