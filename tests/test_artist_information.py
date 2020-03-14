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


def generate_search_responses(times: int):
    search_responses = []
    spotify_search_response = {
        "artists": {
            "items": [
                {
                    "images": [
                        {
                            "height": 640,
                            "url": "https://image_640.com",
                            "width": 640
                        },
                        {
                            "height": 320,
                            "url": "https://image_320.com",
                            "width": 320
                        },
                        {
                            "height": 160,
                            "url": "https://image_160.com",
                            "width": 160
                        }
                    ]
                }
            ]
        }
    }
    for time in range(0, times):
        response_copy = copy.deepcopy(spotify_search_response)
        response_copy["artists"]["items"][0]["images"][1]["url"] = "https://" + str(time) + "image_320.com"
        search_responses.append(response_copy)
    return search_responses


def generate_search_urls(artists: List[str]) -> List[str]:
    search_urls = []
    spotify_search_endpoint = "https://api.spotify.com/v1/search?type=artist&limit=1&q="
    for artist in artists:
        search_urls.append(spotify_search_endpoint + artist)
    return search_urls


def test_get_images_with_empty_list_returns_empty_list():
    assert get_images([]) == []
    assert len(responses.calls) == 0


@responses.activate
def test_get_images_returns_ordered_list_of_image_urls():
    artists = ["Bloodbath", "Megadeth", "Vader"]
    search_urls = generate_search_urls(artists)
    search_responses = generate_search_responses(3)
    authorization_header_key = "Authroization"
    authorization_header_value = "Basic " + b64encode(
        (os.environ["SPOTIFY_CLIENT_ID"] + ":" + os.environ["SPOTIFY_CLIENT_SECRET"]).encode()).decode("utf-8")
    content_type_header_key = "Content-Type"
    content_type_header_value = "application/x-www-form-urlencoded"
    expected_body = "grant_type=client_credentials"

    responses.add(responses.POST, spotify_token_endpoint, json=spotify_token_response, status=200)
    responses.add(responses.GET, "https://api.spotify.com/v1/search", json=search_responses[0], status=200)
    responses.add(responses.GET, "https://api.spotify.com/v1/search", json=search_responses[1], status=200)
    responses.add(responses.GET, "https://api.spotify.com/v1/search", json=search_responses[2], status=200)

    artist_images = get_images(artists)

    assert len(responses.calls) == 4
    assert responses.calls[0].request.url == spotify_token_endpoint
    assert responses.calls[1].request.url == search_urls[0]
    assert responses.calls[2].request.url == search_urls[1]
    assert responses.calls[3].request.url == search_urls[2]

    assert responses.calls[0].request.body == expected_body
    assert authorization_header_key in responses.calls[0].request.headers
    assert content_type_header_key in responses.calls[0].request.headers
    assert responses.calls[0].request.headers[authorization_header_key] == authorization_header_value
    assert responses.calls[0].request.headers[content_type_header_key] == content_type_header_value

    assert authorization_header_key in responses.calls[1].request.headers
    assert authorization_header_key in responses.calls[2].request.headers
    assert authorization_header_key in responses.calls[3].request.headers
    assert responses.calls[1].request.headers[authorization_header_key] == "Bearer token"
    assert responses.calls[2].request.headers[authorization_header_key] == "Bearer token"
    assert responses.calls[3].request.headers[authorization_header_key] == "Bearer token"

    assert ["https://0image_320.com", "https://1image_320.com", "https://2image_320.com"] == artist_images


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
    artists = ["Bloodbath", "Megadeth", "Vader"]
    search_urls = generate_search_urls(artists)
    error_message = {"error": "error"}
    responses.add(responses.POST, spotify_token_endpoint, json=spotify_token_response, status=200)
    responses.add(responses.GET, "https://api.spotify.com/v1/search", json=error_message, status=500)

    with pytest.raises(SpotifyException):
        get_images(artists)

    assert len(responses.calls) == 2
    assert responses.calls[0].request.url == spotify_token_endpoint
    assert responses.calls[1].request.url == search_urls[0]

    assert len(caplog.records) == 1
    for record in caplog.records:
        assert record.levelname == "ERROR"
        assert record.getMessage() == "Spotify search returned status 500, " + str(error_message)
