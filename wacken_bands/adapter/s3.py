import logging

from botocore.exceptions import ClientError


class S3:
    def __init__(self, s3_client) -> None:
        super().__init__()
        self.s3 = s3_client

    def upload(self, *, bucket_name: str, key: str, json: str):
        try:
            self.s3.put_object(Bucket=bucket_name, Key=key, Body=json)
        except ClientError as e:
            logging.error(e)
            raise
