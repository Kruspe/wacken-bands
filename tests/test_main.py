import responses

from src.__main__ import get_bands, ARTISTS_URL


@responses.activate
def test_get_bands_returns_list_of_bands():
    bloodbath = {'artist': {'title': 'Bloodbath'}}
    megadeth = {'artist': {'title': 'Megadeth'}}
    vader = {'artist': {'title': 'Vader'}}
    bands = [bloodbath, megadeth, vader]
    expected_band_names = [bloodbath['artist']['title'], megadeth['artist']['title'], vader['artist']['title']]

    responses.add(responses.GET, ARTISTS_URL, json=bands, status=200)
    assert get_bands() == expected_band_names


@responses.activate
def test_get_bands_returns_empty_list_when_request_is_not_successful():
    responses.add(responses.GET, ARTISTS_URL, status=500)
    assert get_bands() == []
