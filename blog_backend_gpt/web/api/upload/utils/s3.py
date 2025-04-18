from blog_backend_gpt.settings import settings
import boto3
import os
from uuid import uuid4
from fastapi import UploadFile

# Get AWS credentials and region from environment variables
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
BUCKET_NAME = os.getenv("AWS_S3_BUCKET")
ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

s3_client = boto3.client(
    "s3",
    aws_access_key_id=settings.aws_access_key_id,
    aws_secret_access_key=settings.aws_secret_access_key,
    region_name=settings.aws_region,
)

def upload_file_to_s3(file: UploadFile) -> str:
    file_extension = file.filename.split(".")[-1].lower()
    file_key = f"uploads/{uuid4()}.{file_extension}"

    s3_client.upload_fileobj(
        Fileobj=file.file,
        Bucket=settings.aws_s3_bucket,
        Key=file_key,
        ExtraArgs={
            "ContentType": file.content_type,
        },
    )

    return f"https://{settings.aws_s3_bucket}.s3.{settings.aws_region}.amazonaws.com/{file_key}"