import responses
import json
import pytest
from botocore.exceptions import ClientError

from botocore.stub import Stubber
from src.__main__ import get_bands, upload_to_s3, S3_CLIENT


@responses.activate
def test_get_bands_returns_list_of_bands():
    bloodbath = {'artist': {'title': 'Bloodbath'}}
    megadeth = {'artist': {'title': 'Megadeth'}}
    vader = {'artist': {'title': 'Vader'}}
    bands = [bloodbath, megadeth, vader]
    expected_band_names = [bloodbath['artist']['title'], megadeth['artist']['title'], vader['artist']['title']]

    responses.add(responses.GET,
                  'https://www.wacken.com/de/programm/bands/?type=1541083944&tx_woamanager_pi2%5Bfestival%5D=4&tx_woamanager_pi2%5Bperformance%5D=1%2C7&tx_woamanager_pi2%5Baction%5D=list&tx_woamanager_pi2%5Bcontroller%5D=AssetJson&cHash=4aaeb0a4c6c3f83fbdd4013abb42357d',
                  json=bands, status=200)
    assert get_bands() == expected_band_names


@responses.activate
def test_get_bands_returns_empty_list_when_request_is_not_successful():
    responses.add(responses.GET,
                  'https://www.wacken.com/de/programm/bands/?type=1541083944&tx_woamanager_pi2%5Bfestival%5D=4&tx_woamanager_pi2%5Bperformance%5D=1%2C7&tx_woamanager_pi2%5Baction%5D=list&tx_woamanager_pi2%5Bcontroller%5D=AssetJson&cHash=4aaeb0a4c6c3f83fbdd4013abb42357d',
                  status=500)
    assert get_bands() == []


def test_upload_to_s3_uploads_list_of_bands():
    bands = ['Bloodbath', 'Megadeth', 'Vader']
    with Stubber(S3_CLIENT) as s3_stub:
        s3_stub.add_response('put_object', {},
                             {'Body': json.dumps(bands), 'Bucket': 'festival-bands-dev', 'Key': 'wacken.json'})
        upload_to_s3(bands)

    assert s3_stub.assert_no_pending_responses


def test_upload_to_s3_without_empty_list_does_not_upload():
    with Stubber(S3_CLIENT) as s3_stub:
        upload_to_s3([])

    assert s3_stub.assert_no_pending_responses


def test_upload_to_s3_logs_exception(caplog):
    with pytest.raises(ClientError):
        with Stubber(S3_CLIENT) as s3_stub:
            s3_stub.add_client_error('put_object', service_error_code='DEAD', service_message='BUCKET DEAD')
            upload_to_s3(['band'])

    for record in caplog.records:
        assert record.levelname == 'ERROR'
        assert record.getMessage() == 'An error occurred (DEAD) when calling the PutObject operation: BUCKET DEAD'
