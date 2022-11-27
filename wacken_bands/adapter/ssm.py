from typing import List


class Ssm:
    def __init__(self, *, ssm_client) -> None:
        super().__init__()
        self.ssm = ssm_client

    def get_parameters(self, *, parameter_names: List[str]):
        response = self.ssm.get_parameters(Names=parameter_names, WithDecryption=True)
        result = {}
        for p in response["Parameters"]:
            result[p["Name"]] = p["Value"]
        return result
