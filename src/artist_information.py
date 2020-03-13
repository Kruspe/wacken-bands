import logging
import os
from base64 import b64encode
from typing import List

import requests


def get_images(artists: List[str]) -> List[str]:
    artist_images = []
    if len(artists) == 0:
        return []

    encoded_spotify_basic_auth = "Basic " + b64encode(
        (os.environ["SPOTIFY_CLIENT_ID"] + ":" + os.environ["SPOTIFY_CLIENT_SECRET"]).encode()).decode("utf-8")

    spotify_token_response = requests.post("https://accounts.spotify.com/api/token", "grant_type=client_credentials",
                                           headers={"Authroization": encoded_spotify_basic_auth,
                                                    "Content-Type": "application/x-www-form-urlencoded"})
    if spotify_token_response.status_code != 200:
        logging.error("Spotify token endpoint returned status " + str(spotify_token_response.status_code))
        raise SpotifyException("Spotify token response is invalid")

    for artist in artists:
        token = spotify_token_response.json()
        search_response = requests.get("https://api.spotify.com/v1/search",
                                       {"type": "artist", "limit": 1, "q": artist},
                                       headers={"Authroization": "Bearer " + token["access_token"]})
        if search_response.status_code != 200:
            logging.error("Spotify search returned status " + str(search_response.status_code))
            raise SpotifyException("Spotify search response is invalid")
        artist_images.append(search_response.json()["artists"]["items"][0]["images"][1]["url"])
    return artist_images


class SpotifyException(Exception):
    pass
