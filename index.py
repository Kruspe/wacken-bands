import boto3

from wacken_bands.adapter.s3 import S3
from wacken_bands.adapter.ssm import Ssm
from wacken_bands.artist_information import ArtistInformation


def handler(event, context):
    s3_client = boto3.client("s3")
    ssm_client = boto3.client("ssm", "eu-west-1")

    ai_handler = ArtistInformation(ssm=Ssm(ssm_client=ssm_client), s3=S3(s3_client=s3_client))

    artist_names = ai_handler.get_artists()
    images = ai_handler.get_images(artist_names)
    ai_handler.upload_to_s3(images)
