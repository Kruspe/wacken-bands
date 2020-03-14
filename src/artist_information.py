import logging
import os
from base64 import b64encode
from typing import List, Dict

import requests


def get_images(artists: List[str]) -> Dict[str, str]:
    artist_images = {}
    if len(artists) == 0:
        return {}

    encoded_spotify_basic_auth = "Basic " + b64encode(
        (os.environ["SPOTIFY_CLIENT_ID"] + ":" + os.environ["SPOTIFY_CLIENT_SECRET"]).encode()).decode("utf-8")

    spotify_token_response = requests.post("https://accounts.spotify.com/api/token", "grant_type=client_credentials",
                                           headers={"Authorization": encoded_spotify_basic_auth,
                                                    "Content-Type": "application/x-www-form-urlencoded"})
    if spotify_token_response.status_code != 200:
        logging.error("Spotify token endpoint returned status " + str(spotify_token_response.status_code)
                      + ", " + str(spotify_token_response.json()))
        raise SpotifyException("Spotify token response is invalid")

    for artist in artists:
        token = spotify_token_response.json()
        search_response = requests.get("https://api.spotify.com/v1/search",
                                       {"type": "artist", "limit": 1, "q": artist},
                                       headers={"Authorization": "Bearer " + token["access_token"]})
        artist_json = search_response.json()
        if search_response.status_code != 200:
            logging.error("Spotify search returned status " + str(search_response.status_code)
                          + ", " + str(artist_json))
            raise SpotifyException("Spotify search response is invalid")
        if len(artist_json["artists"]["items"]) > 0:
            artist_images[artist] = artist_json["artists"]["items"][0]["images"][1]["url"]
        else:
            artist_images[artist] = None
    return artist_images


class SpotifyException(Exception):
    pass
