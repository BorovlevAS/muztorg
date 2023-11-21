import json

import requests


class APIRequest:

    """Класс для отправки данных и получения из НП"""

    url = "https://api.novaposhta.ua/v2.0/json/"
    headers = {"Content-type": "application/json"}

    @classmethod
    def get_data(cls, data):
        """Отправляет данные и принимает. Если удачно то вернет лист, если ошибка - словарь"""

        data = json.dumps(data)
        # мы тут не используем таймаут, потому отключим проверку pylint
        # pylint: disable=external-request-timeout
        response = requests.post(url=cls.url, data=data, headers=cls.headers)
        deserialized_response = json.loads(response.text)
        if deserialized_response["success"]:
            return deserialized_response["data"]
        else:
            return {
                "info": deserialized_response["info"],
                "errors": deserialized_response["errors"],
                "warnings": deserialized_response["warnings"],
            }


if __name__ == "__main__":
    data = {
        "modelName": "Common",
        "calledMethod": "getPackList",
        "methodProperties": {
            "Length": "",
            "Width": "",
            "Height": "",
            "TypeOfPacking": "",
        },
        "apiKey": "",
    }
