import copy
import os
from base64 import b64encode
from typing import List

import pytest
import responses

from src.artist_information import get_images, SpotifyException

spotify_token_endpoint = "https://accounts.spotify.com/api/token"
spotify_token_response = {
    "access_token": "token",
    "token_type": "bearer",
    "expires_in": 3600,
}
expected_bloodbath_image_url = "https://bloodbath_image.com"
bloodbath_search_response = {
    "artists": {
        "items": [
            {
                "images": [
                    {
                        "height": 640,
                        "url": expected_bloodbath_image_url,
                        "width": 640
                    },
                ],
                "name": "Bloodbath",
            },
        ],
    }
}


def test_get_images_with_empty_list_empty_dict():
    assert get_images([]) == {}
    assert len(responses.calls) == 0


@responses.activate
def test_get_images_raises_and_logs_exception_when_getting_token_fails(caplog):
    error_message = {"error": "error"}
    responses.add(responses.POST, spotify_token_endpoint, json=error_message, status=500)

    with pytest.raises(SpotifyException):
        get_images(["Bloodbath"])

    assert len(responses.calls) == 1
    assert responses.calls[0].request.url == spotify_token_endpoint

    assert len(caplog.records) == 1
    for record in caplog.records:
        assert record.levelname == "ERROR"
        expected_log_message = 'Spotify token endpoint returned status 500, ' + str(error_message)
        assert record.getMessage() == expected_log_message


@responses.activate
def test_get_images_raises_and_logs_exception_when_search_fails(caplog):
    error_message = {"error": "error"}
    responses.add(responses.POST, spotify_token_endpoint, json=spotify_token_response, status=200)
    responses.add(responses.GET, "https://api.spotify.com/v1/search", json=error_message, status=500)

    with pytest.raises(SpotifyException):
        get_images(["Bloodbath"])

    assert len(responses.calls) == 2
    assert responses.calls[0].request.url == spotify_token_endpoint
    assert responses.calls[1].request.url == "https://api.spotify.com/v1/search?type=artist&limit=5&q=Bloodbath"

    assert len(caplog.records) == 1
    for record in caplog.records:
        assert record.levelname == "ERROR"
        assert record.getMessage() == "Spotify search returned status 500, " + str(error_message)


@responses.activate
def test_get_images_endpoints_get_called_correctly():
    authorization_header_key = "Authorization"
    authorization_header_value = "Basic " + b64encode(
        (os.environ["SPOTIFY_CLIENT_ID"] + ":" + os.environ["SPOTIFY_CLIENT_SECRET"]).encode()).decode("utf-8")
    content_type_header_key = "Content-Type"
    content_type_header_value = "application/x-www-form-urlencoded"
    expected_body = "grant_type=client_credentials"

    responses.add(responses.POST, spotify_token_endpoint, json=spotify_token_response, status=200)
    responses.add(responses.GET, "https://api.spotify.com/v1/search", json=bloodbath_search_response, status=200)

    get_images(["Bloodbath"])

    assert len(responses.calls) == 2
    assert responses.calls[0].request.url == spotify_token_endpoint
    assert responses.calls[1].request.url == "https://api.spotify.com/v1/search?type=artist&limit=5&q=Bloodbath"

    assert responses.calls[0].request.body == expected_body
    assert authorization_header_key in responses.calls[0].request.headers
    assert content_type_header_key in responses.calls[0].request.headers
    assert responses.calls[0].request.headers[authorization_header_key] == authorization_header_value
    assert responses.calls[0].request.headers[content_type_header_key] == content_type_header_value

    assert authorization_header_key in responses.calls[1].request.headers
    assert responses.calls[1].request.headers[authorization_header_key] == "Bearer token"


@responses.activate
def test_get_images_returns_correct_images_for_two_bands():
    expected_megadeth_image_url = "https://megadeth_image.com"
    megadeth_search_response = copy.deepcopy(bloodbath_search_response)
    megadeth_search_response["artists"]["items"][0]["name"] = "Megadeth"
    megadeth_search_response["artists"]["items"][0]["images"][0]["url"] = expected_megadeth_image_url

    responses.add(responses.POST, spotify_token_endpoint, json=spotify_token_response, status=200)
    responses.add(responses.GET, "https://api.spotify.com/v1/search", json=bloodbath_search_response, status=200)
    responses.add(responses.GET, "https://api.spotify.com/v1/search", json=megadeth_search_response, status=200)

    artist_images = get_images(["Bloodbath", "Megadeth"])

    assert len(responses.calls) == 3

    assert artist_images == {"Bloodbath": expected_bloodbath_image_url, "Megadeth": expected_megadeth_image_url}


@responses.activate
def test_get_images_returns_none_when_no_artist_was_found():
    search_response = {
        "artists": {
            "items": [],
        }
    }
    responses.add(responses.POST, spotify_token_endpoint, json=spotify_token_response, status=200)
    responses.add(responses.GET, "https://api.spotify.com/v1/search", json=search_response, status=200)

    artist_images = get_images(["Bloodbath"])

    assert len(responses.calls) == 2

    assert artist_images == {"Bloodbath": None}


@responses.activate
def test_get_images_returns_none_when_no_name_matches_search():
    search_response = {
        "artists": {
            "items": [
                {
                    "images": [],
                    "name": "NoMatch",
                },
            ],
        }
    }
    responses.add(responses.POST, spotify_token_endpoint, json=spotify_token_response, status=200)
    responses.add(responses.GET, "https://api.spotify.com/v1/search", json=search_response, status=200)

    artist_images = get_images(["Attic"])

    assert len(responses.calls) == 2

    assert artist_images == {"Attic": None}


@responses.activate
def test_get_images_returns_first_image_for_matching_name():
    expected_image_url = "https://expected_image.com"
    search_response_with_two_name_matches = copy.deepcopy(bloodbath_search_response)
    search_response_with_two_name_matches["artists"]["items"][0]["images"][0]["url"] = expected_image_url
    search_response_with_two_name_matches["artists"]["items"].append(
        {
            "images": [
                {
                    "height": 300,
                    "url": "https://different_image.com",
                    "width": 300
                },
            ],
            "name": "Bloodbath",
        }
    )

    responses.add(responses.POST, spotify_token_endpoint, json=spotify_token_response, status=200)
    responses.add(responses.GET, "https://api.spotify.com/v1/search", json=search_response_with_two_name_matches,
                  status=200)

    artist_images = get_images(["Bloodbath"])

    assert len(responses.calls) == 2

    assert artist_images == {"Bloodbath": expected_image_url}


@responses.activate
def test_get_images_returns_first_image_that_is_greater_than_400_in_width_and_height():
    search_response = {
        "artists": {
            "items": [
                {
                    "images": [
                        {
                            "height": 1000,
                            "url": "https://too_big_image.com",
                            "width": 1000
                        },
                        {
                            "height": 300,
                            "url": expected_bloodbath_image_url,
                            "width": 300
                        },
                        {
                            "height": 420,
                            "url": "https://width_too_small.com",
                            "width": 120
                        },
                        {
                            "height": 120,
                            "url": "https://too_small_image.com",
                            "width": 120
                        }
                    ],
                    "name": "Bloodbath"
                }
            ]
        }
    }

    responses.add(responses.POST, spotify_token_endpoint, json=spotify_token_response, status=200)
    responses.add(responses.GET, "https://api.spotify.com/v1/search", json=search_response, status=200)

    artist_images = get_images(["Bloodbath"])

    assert len(responses.calls) == 2

    assert artist_images == {"Bloodbath": expected_bloodbath_image_url}

@responses.activate
def test_get_images_returns_none_when_no_image_bigger_than_299_was_found():
    search_response = {
        "artists": {
            "items": [
                {
                    "images": [
                        {
                            "height": 299,
                            "url": "https://too_small_image.com",
                            "width": 299
                        }
                    ],
                    "name": "Bloodbath",
                },
            ],
        }
    }
    responses.add(responses.POST, spotify_token_endpoint, json=spotify_token_response, status=200)
    responses.add(responses.GET, "https://api.spotify.com/v1/search", json=search_response, status=200)

    artist_images = get_images(["Bloodbath"])

    assert len(responses.calls) == 2

    assert artist_images == {"Bloodbath": None}


@responses.activate
def test_get_images_returns_none_when_no_images_were_found():
    search_response = {
        "artists": {
            "items": [
                {
                    "images": [],
                    "name": "Bloodbath",
                },
            ],
        }
    }
    responses.add(responses.POST, spotify_token_endpoint, json=spotify_token_response, status=200)
    responses.add(responses.GET, "https://api.spotify.com/v1/search", json=search_response, status=200)

    artist_images = get_images(["Bloodbath"])

    assert len(responses.calls) == 2

    assert artist_images == {"Bloodbath": None}


@responses.activate
def test_get_images_returns_image_only_for_matching_name():
    expected_image_url = "https://attic_image.com"
    search_response = {
        "artists": {
            "items": [
                {
                    "images": [],
                    "name": "Atticus Ross",
                },
                {
                    "images": [],
                    "name": "Attic109",
                },
                {
                    "images": [
                        {
                            "height": 640,
                            "url": expected_image_url,
                            "width": 640
                        },
                    ],
                    "name": "Attic",
                },
                {
                    "images": [],
                    "name": "Atticus",
                },
                {
                    "images": [],
                    "name": "Attica Bars",
                }
            ],
        }
    }
    responses.add(responses.POST, spotify_token_endpoint, json=spotify_token_response, status=200)
    responses.add(responses.GET, "https://api.spotify.com/v1/search", json=search_response, status=200)

    artist_images = get_images(["Attic"])

    assert len(responses.calls) == 2

    assert artist_images == {"Attic": expected_image_url}
