import responses
import json

from botocore.stub import Stubber
from src.__main__ import get_bands, ARTISTS_URL, upload_to_s3, S3_CLIENT, BUCKET_NAME, BUCKET_KEY


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


def test_upload_to_s3_uploads_list_of_bands():
    bands = ['Bloodbath', 'Megadeth', 'Vader']
    with Stubber(S3_CLIENT) as s3_stub:
        s3_stub.add_response('put_object', {},
                             {'Body': json.dumps(bands), 'Bucket': BUCKET_NAME, 'Key': BUCKET_KEY})
        upload_to_s3(bands)

    assert s3_stub.assert_no_pending_responses


def test_upload_to_s3_without_empty_list_does_not_upload():
    with Stubber(S3_CLIENT) as s3_stub:
        upload_to_s3([])

    assert s3_stub.assert_no_pending_responses


def test_upload_to_s3_logs_exception(caplog):
    with Stubber(S3_CLIENT) as s3_stub:
        s3_stub.add_client_error('put_object', service_error_code='DEAD', service_message='BUCKET DEAD')
        upload_to_s3(['band'])

    for record in caplog.records:
        assert record.levelname == 'ERROR'
        assert record.getMessage() == 'An error occurred (DEAD) when calling the PutObject operation: BUCKET DEAD'
