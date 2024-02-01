import logging

import requests

_logger = logging.getLogger(__name__)


class MTApi:
    def __init__(self, URI, endpoint):
        self.URI = URI
        self.endpoint = endpoint
        self.headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        }
        # {"Content-Type": "application/json"}

    def __str__(self):
        return """URI: {}
        ENDPOINT: {}
        """.format(
            self.URI,
            self.endpoint,
        )

    def send_data(self, message):
        try:
            _logger.debug("==== MTApi: sending data: %s", message)
            # URI = posixpath.join(self.URI, self.endpoint)
            # reply = requests.post(url=URI, headers=self.headers, data=message)
            reply = requests.get(
                url=self.URI,
                headers=self.headers,
                timeout=10.0,
            )
            result = reply.json()
            if result.get("status") != "success":
                _logger.error(
                    """MTApi: error sending data:
                    API: %s
                    DATA: %s
                    result: %s
                    """,
                    self,
                    message,
                    result,
                )
            else:
                _logger.debug("==== MTApi: data was sent: %s", message)
        except Exception as exc:
            _logger.exception(
                """MTApi error:
                API: %s
                DATA: %s
                exception: %s
                """,
                self,
                message,
                exc,
            )

    def import_data(self):
        # headers = {
        #     "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        # }

        # url = "https://muztorg.ua/index.php?route=dwebexporter/exporting&id=orders"
        # response = requests.get(self.URI, headers=self.headers, timeout=10)
        # print(response.status_code)

        try:
            _logger.debug("==== MTApi: import data: %s", self.URI)
            # URI = posixpath.join(self.URI, self.endpoint)
            # reply = requests.post(url=URI, headers=self.headers, data=message)
            reply = requests.get(
                url=self.URI,
                headers=self.headers,
                timeout=10.0,
            )
            # result = reply.json()
            # if result.get("status") != "success":
            #     _logger.error(
            #         """MTApi: error sending data:
            #         API: %s
            #         DATA: %s
            #         result: %s
            #         """,
            #         self,
            #         self.URI,
            #         result,
            #     )
            # else:
            #     _logger.debug("==== MTApi: data was sent: %s", self.url)
            return reply
        except Exception as exc:
            _logger.exception(
                """MTApi error:
                API: %s
                DATA: %s
                exception: %s
                """,
                self,
                self.URI,
                exc,
            )

            return None

    # if __name__ == "__main__":
    #     import_data()
