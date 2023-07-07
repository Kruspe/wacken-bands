import json
import os

import boto3
import pytest
import responses
from moto import mock_ssm, mock_s3
from mypy_boto3_s3 import S3Client

from index import handler


@pytest.fixture
def setup_env():
    os.environ["SPOTIFY_CLIENT_ID_PARAMETER_NAME"] = "/spotify/client-id"
    os.environ["SPOTIFY_CLIENT_SECRET_PARAMETER_NAME"] = "/spotify/client-secret"
    os.environ["FESTIVAL_ARTISTS_BUCKET"] = "bucket-name"
    yield
    del os.environ["SPOTIFY_CLIENT_ID_PARAMETER_NAME"]
    del os.environ["SPOTIFY_CLIENT_SECRET_PARAMETER_NAME"]
    del os.environ["FESTIVAL_ARTISTS_BUCKET"]


@mock_s3
@mock_ssm
@responses.activate
def test_get_bands_handler_gets_artists_and_images_and_uploads_them(setup_env):
    wacken_bloodbath_response = [{"artist": {"title": "Bloodbath"}}]
    spotify_token_endpoint = "https://accounts.spotify.com/api/token"
    spotify_token_response = {
        "access_token": "token",
        "token_type": "bearer",
        "expires_in": 3600,
    }
    spotify_search_bloodbath_url = (
        "https://api.spotify.com/v1/search?type=artist&limit=5&q=Bloodbath"
    )
    spotify_search_bloodbath_response = {
        "artists": {
            "items": [
                {
                    "images": [
                        {"height": 640, "url": "https://image_640.com", "width": 640},
                        {"height": 320, "url": "https://image_320.com", "width": 320},
                        {"height": 160, "url": "https://image_160.com", "width": 160},
                    ],
                    "name": "Bloodbath",
                }
            ]
        }
    }
    responses.add(
        responses.GET,
        "https://www.wacken.com/fileadmin/Json/bandlist-concert.json",
        json=wacken_bloodbath_response,
        status=200,
    )
    responses.add(
        responses.POST, spotify_token_endpoint, json=spotify_token_response, status=200
    )
    responses.add(
        responses.GET,
        spotify_search_bloodbath_url,
        json=spotify_search_bloodbath_response,
        status=200,
    )

    s3_client: S3Client = boto3.client("s3")
    s3_client.create_bucket(
        Bucket="bucket-name",
        CreateBucketConfiguration={"LocationConstraint": "eu-west-1"},
    )

    ssm_client = boto3.client("ssm", "eu-west-1")
    ssm_client.put_parameter(
        Name="/spotify/client-id", Value="value1", Type="SecureString"
    )
    ssm_client.put_parameter(
        Name="/spotify/client-secret", Value="value2", Type="SecureString"
    )

    expected_json = [{"artist": "Bloodbath", "image": "https://image_320.com"}]

    handler(None, None)

    uploaded_file = s3_client.get_object(Bucket="bucket-name", Key="wacken.json")

    assert expected_json == json.load(uploaded_file.get("Body"))
