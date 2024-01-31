import logging
import posixpath

import requests

_logger = logging.getLogger(__name__)


class MTApi:
    def __init__(self, URI, endpoint):
        self.URI = URI
        self.endpoint = endpoint
        self.headers = {"Content-Type": "application/json"}

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
            URI = posixpath.join(self.URI, self.endpoint)
            # reply = requests.post(url=URI, headers=self.headers, data=message)
            reply = requests.get(
                url=URI,
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
