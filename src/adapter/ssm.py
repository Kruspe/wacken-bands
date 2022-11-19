from typing import List, TYPE_CHECKING
from mypy_boto3_ssm.type_defs import GetParametersResultTypeDef

if TYPE_CHECKING:
    from mypy_boto3_ssm.client import SSMClient


class Ssm:
    def __init__(self, *, ssm_client: "SSMClient") -> None:
        super().__init__()
        self.ssm = ssm_client

    def get_parameters(self, *, parameter_names: List[str]):
        response: GetParametersResultTypeDef = self.ssm.get_parameters(Names=parameter_names, WithDecryption=True)
        result = {}
        for p in response["Parameters"]:
            result[p["Name"]] = p["Value"]
        return result
