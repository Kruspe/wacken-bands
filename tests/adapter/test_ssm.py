import boto3
from moto import mock_ssm

from wacken_bands.adapter.ssm import Ssm


@mock_ssm
def test_ssm_get_parameters_returns_parameter_values():
    ssm_client = boto3.client("ssm", "eu-west-1")
    ssm_client.put_parameter(Name="parameter1", Value="value1", Type="SecureString")
    ssm_client.put_parameter(Name="parameter2", Value="value2", Type="SecureString")

    ssm = Ssm(ssm_client=ssm_client)
    response = ssm.get_parameters(parameter_names=["parameter1", "parameter2", "invalid"])
    assert response == {
        "parameter1": "value1",
        "parameter2": "value2",
    }
