from typing import List
import requests

ARTISTS_URL = 'https://www.wacken.com/de/programm/bands/?type=1541083944&tx_woamanager_pi2%5Bfestival%5D=4&tx_woamanager_pi2%5Bperformance%5D=1%2C7&tx_woamanager_pi2%5Baction%5D=list&tx_woamanager_pi2%5Bcontroller%5D=AssetJson&cHash=4aaeb0a4c6c3f83fbdd4013abb42357d'


def get_bands_handler(event, context):
    return get_bands()


def get_bands() -> List[str]:
    band_names = []
    response = requests.get(ARTISTS_URL)
    if response.status_code == 200:
        bands = response.json()
        for band in bands:
            band_names.append(band['artist']['title'])

    return band_names
