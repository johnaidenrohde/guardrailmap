from uuid import uuid4

import boto3
from botocore.client import Config

from .config import settings


def upload_photo(file_bytes: bytes, content_type: str, original_name: str) -> tuple[str, str]:
    if not all([settings.spaces_bucket, settings.spaces_key, settings.spaces_secret, settings.spaces_endpoint_url]):
        raise RuntimeError('DigitalOcean Spaces is not configured')

    extension = original_name.rsplit('.', 1)[-1].lower() if '.' in original_name else 'jpg'
    object_key = f'guardrail-photos/{uuid4().hex}.{extension}'

    client = boto3.client(
        's3',
        endpoint_url=settings.spaces_endpoint_url,
        region_name=settings.spaces_region,
        aws_access_key_id=settings.spaces_key,
        aws_secret_access_key=settings.spaces_secret,
        config=Config(signature_version='s3v4'),
    )

    client.put_object(
        Bucket=settings.spaces_bucket,
        Key=object_key,
        Body=file_bytes,
        ACL='public-read',
        ContentType=content_type,
    )

    if settings.spaces_public_base_url:
        public_url = f"{settings.spaces_public_base_url.rstrip('/')}/{object_key}"
    else:
        public_url = f"{settings.spaces_endpoint_url.rstrip('/')}/{settings.spaces_bucket}/{object_key}"

    return object_key, public_url
