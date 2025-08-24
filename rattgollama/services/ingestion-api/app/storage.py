import os
import boto3
from botocore.exceptions import ClientError
from typing import BinaryIO

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
BUCKET_NAME = "documents"

def get_s3_client():
    return boto3.client(
        's3',
        endpoint_url=f"http://{MINIO_ENDPOINT}",
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY,
        region_name='us-east-1'
    )

def ensure_bucket_exists():
    s3_client = get_s3_client()
    try:
        s3_client.head_bucket(Bucket=BUCKET_NAME)
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            try:
                s3_client.create_bucket(Bucket=BUCKET_NAME)
            except ClientError as create_error:
                print(f"Error creating bucket: {create_error}")
        else:
            print(f"Error checking bucket: {e}")

def upload_file(file_obj: BinaryIO, object_key: str) -> bool:
    s3_client = get_s3_client()
    try:
        s3_client.upload_fileobj(file_obj, BUCKET_NAME, object_key)
        return True
    except ClientError as e:
        print(f"Error uploading file: {e}")
        return False

def download_file(object_key: str) -> bytes:
    s3_client = get_s3_client()
    try:
        response = s3_client.get_object(Bucket=BUCKET_NAME, Key=object_key)
        return response['Body'].read()
    except ClientError as e:
        print(f"Error downloading file: {e}")
        return None