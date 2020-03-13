from typing import List, Dict
import requests
import boto3
import logging
import json

from botocore.exceptions import ClientError

S3_CLIENT = boto3.client('s3')


def get_bands_handler(event, context):
    bands = get_artists()
    upload_to_s3(bands)


def get_artists() -> List[str]:
    artist_names = []
    response = requests.get(
        'https://www.wacken.com/de/programm/bands/?type=1541083944&tx_woamanager_pi2%5Bfestival%5D=4&tx_woamanager_pi2%5Bperformance%5D=1%2C7&tx_woamanager_pi2%5Baction%5D=list&tx_woamanager_pi2%5Bcontroller%5D=AssetJson&cHash=4aaeb0a4c6c3f83fbdd4013abb42357d')
    if response.status_code == 200:
        artists = response.json()
        for artist in artists:
            artist_names.append(artist['artist']['title'])

    return artist_names


def upload_to_s3(artists: List[Dict[str, str]]):
    if artists:
        try:
            S3_CLIENT.put_object(Bucket='festival-bandsprod-prod', Key='public/wacken.json', Body=json.dumps(artists))
        except ClientError as e:
            logging.error(e)
            raise
