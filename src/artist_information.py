import itertools
import logging
import os
from base64 import b64encode
from typing import List, Dict

import requests


def get_images(artists: List[str]) -> Dict[str, str]:
    if len(artists) == 0:
        return {}

    artist_images = {}
    encoded_spotify_basic_auth = "Basic " + b64encode(
        (os.environ["SPOTIFY_CLIENT_ID"] + ":" + os.environ["SPOTIFY_CLIENT_SECRET"]).encode()).decode("utf-8")

    spotify_token_response = requests.post("https://accounts.spotify.com/api/token", "grant_type=client_credentials",
                                           headers={"Authorization": encoded_spotify_basic_auth,
                                                    "Content-Type": "application/x-www-form-urlencoded"})
    token_response_status_code = spotify_token_response.status_code
    token_response_json = spotify_token_response.json()

    if token_response_status_code != 200:
        logging.error("Spotify token endpoint returned status " + str(token_response_status_code)
                      + ", " + str(token_response_json))
        raise SpotifyException("Spotify token response is invalid")

    for artist in artists:
        search_response = requests.get("https://api.spotify.com/v1/search",
                                       {"type": "artist", "limit": 5, "q": artist},
                                       headers={"Authorization": "Bearer " + token_response_json["access_token"]})
        search_response_status_code = search_response.status_code
        search_response_json = search_response.json()

        if search_response_status_code != 200:
            logging.error("Spotify search returned status " + str(search_response_status_code)
                          + ", " + str(search_response_json))
            raise SpotifyException("Spotify search response is invalid")

        found_artists = search_response_json["artists"]["items"]
        if len(found_artists) == 0:
            artist_images[artist] = None
            continue

        matching_artists = find_artists_with_matching_name(found_artists, artist)
        if len(matching_artists) == 0:
            artist_images[artist] = None
            continue
        matching_artists_with_images = find_artists_with_images(matching_artists)
        if len(matching_artists_with_images) == 0:
            artist_images[artist] = None
            continue

        artist_images_with_correct_size = get_images_with_size_greater_300(matching_artists_with_images[0])
        amount_of_images = len(artist_images_with_correct_size)
        if amount_of_images == 0:
            artist_images[artist] = None
            continue

        artist_images[artist] = artist_images_with_correct_size[amount_of_images - 1]["url"]

    return artist_images


def find_artists_with_matching_name(search_result, name):
    return list(itertools.filterfalse(
        lambda found_artist: found_artist["name"].lower() != name.lower(), search_result))


def find_artists_with_images(artists):
    return list(itertools.filterfalse(
        lambda artist: len(artist["images"]) == 0, artists))


def get_images_with_size_greater_300(artist):
    return list(itertools.filterfalse(
        lambda image: image["width"] < 300 or image["height"] < 300, artist["images"]))


class SpotifyException(Exception):
    pass
