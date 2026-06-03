from io import BytesIO
from typing import BinaryIO

import boto3
from botocore.exceptions import ClientError
from app.core.config import settings

_client = None

def get_storage_client():
    global _client
    if _client is None:
        _client = boto3.client(
            "s3",
            endpoint_url=f"http://{settings.MINIO_ENDPOINT}",
            aws_access_key_id=settings.MINIO_ACCESS_KEY,
            aws_secret_access_key=settings.MINIO_SECRET_KEY,
            region_name="us-east-1",
        )

    return _client

def ensure_bucket_exists() -> None:
    client = get_storage_client()

    try:
        client.head_bucket(Bucket=settings.MINIO_BUCKET)

    except ClientError:
        client.create_bucket(Bucket=settings.MINIO_BUCKET)

def upload_file(file_obj: BinaryIO, key: str) -> str:
    get_storage_client().upload_fileobj(file_obj, settings.MINIO_BUCKET, key)
    return key

def download_file(key: str) -> BytesIO:
    buf = BytesIO()
    get_storage_client().download_fileobj(settings.MINIO_BUCKET, key, buf)
    buf.seek(0)
    return buf

def delete_file(key: str) -> None:
    get_storage_client().delete_object(Bucket=settings.MINIO_BUCKET, Key=key)

def get_presigned_url(key: str, expires_in: int=3600) -> str:
    return get_storage_client().generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.MINIO_BUCKET, "Key": key},
        ExpiresIn=expires_in
    )