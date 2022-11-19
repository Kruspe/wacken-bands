import boto3
import pytest
from botocore.exceptions import ClientError
from moto import mock_s3

from src.adapter.s3 import S3


@mock_s3
def test_upload_uploads_to_s3():
    s3_client = boto3.client("s3")
    s3_client.create_bucket(Bucket="bucket-name")
    s3 = S3(s3_client=s3_client)

    s3.upload(bucket_name="bucket-name", key="key", json="json")

    uploaded_object = s3_client.get_object(Bucket="bucket-name", Key="key")
    assert uploaded_object["Body"].read().decode("utf-8") == "json"


@mock_s3
def test_upload_logs_exception(caplog):
    s3 = S3(boto3.client("s3"))

    with pytest.raises(ClientError):
        s3.upload(bucket_name="bucket-name", key="key", json="json")

    assert len(caplog.records) == 1
    for record in caplog.records:
        assert record.levelname == "ERROR"
        assert record.getMessage() == "An error occurred (NoSuchBucket) when calling the PutObject operation: The specified bucket does not exist"
