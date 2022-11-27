import itertools
import json
import logging
import os
from base64 import b64encode
from typing import List, Dict

import requests

from wacken_bands.adapter.s3 import S3
from wacken_bands.adapter.ssm import Ssm


class ArtistInformation:
    def __init__(self, *, ssm: Ssm, s3: S3) -> None:
        super().__init__()
        self.ssm = ssm
        self.s3 = s3

    def get_artists(self) -> List[str]:
        artist_names = []
        response = requests.get("https://www.wacken.com/fileadmin/Json/bandlist-concert.json")
        if response.status_code == 200:
            artists = response.json()
            for artist in artists:
                artist_names.append(artist["artist"]["title"])
        return artist_names

    def get_images(self, *, artist_names: List[str]) -> Dict:
        if len(artist_names) == 0:
            return {}

        spotify_client_id_parameter_name = os.environ["SPOTIFY_CLIENT_ID_PARAMETER_NAME"]
        spotify_client_secret_parameter_name = os.environ["SPOTIFY_CLIENT_SECRET_PARAMETER_NAME"]
        spotify_secrets = self.ssm.get_parameters(parameter_names=[spotify_client_id_parameter_name, spotify_client_secret_parameter_name])
        encoded_spotify_basic_auth = "Basic " + b64encode(
            (spotify_secrets[spotify_client_id_parameter_name] + ":" + spotify_secrets[spotify_client_secret_parameter_name]).encode()
        ).decode("utf-8")
        spotify_token_response = requests.post(
            "https://accounts.spotify.com/api/token",
            "grant_type=client_credentials",
            headers={"Authorization": encoded_spotify_basic_auth, "Content-Type": "application/x-www-form-urlencoded"},
        )
        token_response_status_code = spotify_token_response.status_code
        token_response_json = spotify_token_response.json()

        if token_response_status_code != 200:
            logging.error("Spotify token endpoint returned status " + str(token_response_status_code) + ", " + str(token_response_json))
            raise SpotifyException("Spotify token response is invalid")

        artist_images = {}

        for artist in artist_names:
            search_response = requests.get(
                "https://api.spotify.com/v1/search",
                {"type": "artist", "limit": 5, "q": artist},
                headers={"Authorization": "Bearer " + token_response_json["access_token"]},
            )
            search_response_status_code = search_response.status_code
            search_response_json = search_response.json()

            if search_response_status_code != 200:
                logging.error("Spotify search returned status " + str(search_response_status_code) + ", " + str(search_response_json))
                raise SpotifyException("Spotify search response is invalid")

            found_artists = search_response_json["artists"]["items"]
            if len(found_artists) == 0:
                artist_images[artist] = None
                continue

            matching_artists = self._find_artists_with_matching_name(found_artists, artist)
            if len(matching_artists) == 0:
                artist_images[artist] = None
                continue
            matching_artists_with_images = self._find_artists_with_images(matching_artists)
            if len(matching_artists_with_images) == 0:
                artist_images[artist] = None
                continue

            artist_images_with_correct_size = self._get_images_with_size_greater_300(matching_artists_with_images[0])
            amount_of_images = len(artist_images_with_correct_size)
            if amount_of_images == 0:
                artist_images[artist] = None
                continue

            artist_images[artist] = artist_images_with_correct_size[amount_of_images - 1]["url"]

        return artist_images

    def upload_to_s3(self, *, artist_images: Dict[str, str]):
        if artist_images:
            result = []
            for artist, image in artist_images.items():
                result.append({"artist": artist, "image": image})
            self.s3.upload(bucket_name=os.getenv("FESTIVAL_BANDS_BUCKET"), key="wacken.json", json=json.dumps(result))

    @staticmethod
    def _find_artists_with_matching_name(search_result, name):
        return list(itertools.filterfalse(lambda found_artist: found_artist["name"].lower() != name.lower(), search_result))

    @staticmethod
    def _find_artists_with_images(artists):
        return list(itertools.filterfalse(lambda artist: len(artist["images"]) == 0, artists))

    @staticmethod
    def _get_images_with_size_greater_300(artist):
        return list(itertools.filterfalse(lambda image: image["width"] < 300 or image["height"] < 300, artist["images"]))


class SpotifyException(Exception):
    pass
