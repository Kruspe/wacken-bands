from typing import List
import requests
import boto3
import logging
import json

from botocore.exceptions import ClientError

S3_CLIENT = boto3.client('s3')


def get_bands_handler(event, context):
    upload_to_s3(get_bands())


def get_bands() -> List[str]:
    band_names = []
    response = requests.get(
        'https://www.wacken.com/de/programm/bands/?type=1541083944&tx_woamanager_pi2%5Bfestival%5D=4&tx_woamanager_pi2%5Bperformance%5D=1%2C7&tx_woamanager_pi2%5Baction%5D=list&tx_woamanager_pi2%5Bcontroller%5D=AssetJson&cHash=4aaeb0a4c6c3f83fbdd4013abb42357d')
    if response.status_code == 200:
        bands = response.json()
        for band in bands:
            band_names.append(band['artist']['title'])

    return band_names


def upload_to_s3(bands: List[str]):
    if bands:
        try:
            S3_CLIENT.put_object(Bucket='festival-bands-dev', Key='public/wacken.json', Body=json.dumps(bands))
        except ClientError as e:
            logging.error(e)
            raise e
