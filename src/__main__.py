import boto3

from src.adapter.s3 import S3
from src.adapter.ssm import Ssm
from src.artist_information_handler import ArtistInformationHandler

s3_client = boto3.client("s3")
ssm_client = boto3.client("ssm", "eu-west-1")

handler = ArtistInformationHandler(ssm=Ssm(ssm_client=ssm_client), s3=S3(s3_client=s3_client))
