import requests


class CheckboxAPI:
    def __init__(self, api_url, api_port, cb_license, mode, access_token=None):
        self.mode = mode
        api_url = api_url.strip()
        if api_url[-1] == "/":
            api_url = api_url[:-1]
        if mode == "checkbox_kassa":
            api_url = api_url + ":" + str(api_port)
        self.api_url = api_url
        self.license = cb_license
        self.access_token = access_token

    def send_request(self, endpoint, method, payload, headers=None):
        if not headers:
            headers = {}
        headers.update(
            {
                "accept": "application/json",
                "Content-Type": "application/json",
            }
        )
        r = requests.request(
            method,
            self.api_url + endpoint,
            headers=headers,
            json=payload,
            timeout=5,
        )

        return r

    def cashier_signin(self, login, password):
        if self.mode == "checkbox_kassa":
            return {"text": "", "access_token": "", "ok": True}

        payload = {
            "login": login,
            "password": password,
        }
        result = self.send_request("/api/v1/cashier/signin", "POST", payload)

        if result.ok:
            return {
                "text": result.text,
                "access_token": result.json()["access_token"],
                "ok": True,
            }
        else:
            return {"error_msg": result.text, "ok": False}

    def cashier_signout(self):
        if self.mode == "checkbox_kassa":
            return {"text": "", "ok": True}

        headers = {
            "Authorization": "Bearer %s" % self.access_token,
        }

        result = self.send_request(
            "/api/v1/cashier/signout",
            "POST",
            payload={},
            headers=headers,
        )

        return {"text": result.text, "ok": result.ok}

    def shift_create(self):
        if self.mode == "checkbox_kassa":
            endpoint = "/api/v1/shift/open"
            headers = {}
        else:
            headers = {
                "Authorization": "Bearer %s" % self.access_token,
                "X-License-Key": self.license,
            }
            endpoint = "/api/v1/shifts"

        result = self.send_request(
            endpoint,
            "POST",
            payload={},
            headers=headers,
        )
        return {"text": result.text, "ok": result.ok}

    def shift_close(self):
        if self.mode == "checkbox_kassa":
            endpoint = "/api/v1/shift/close"
            headers = {}
        else:
            headers = {
                "Authorization": "Bearer %s" % self.access_token,
            }
            endpoint = "/api/v1/shifts/close"

        result = self.send_request(
            endpoint,
            "POST",
            payload={},
            headers=headers,
        )
        return {"text": result.text, "ok": result.ok}

    def service_receipt(self, amount):
        if self.mode == "checkbox_kassa":
            endpoint = "/api/v1/receipt/service"
            headers = {}
        else:
            endpoint = "/api/v1/receipts/service"
            headers = {
                "Authorization": "Bearer %s" % self.access_token,
            }

        payload = {
            "payment": {
                "type": "CASH",
                "value": amount * 100,
                "label": "Готівка",
            },
        }

        result = self.send_request(
            endpoint,
            "POST",
            payload=payload,
            headers=headers,
        )
        return {"text": result.text, "ok": result.ok}

    def reports_xreport(self):
        if self.mode == "checkbox_kassa":
            endpoint = "/api/v1/shift/xreport/txt"
            headers = {}
            result = self.send_request(
                endpoint,
                "POST",
                payload={},
                headers=headers,
            )
            return {"text": result.text, "ok": result.ok}
        else:
            endpoint = "/api/v1/reports"
            headers = {
                "Authorization": "Bearer " + self.checkbox_access_token,
            }
            result = self.send_request(
                endpoint,
                "POST",
                payload={},
                headers=headers,
            )
            response_json = result.json()
            if not response_json.get("id", False):
                return {"ok": False, "text": "No report id"}

            report_id = response_json["id"]
            endpoint = f"/api/v1/reports/{report_id}/text"
            result = self.send_request(
                endpoint,
                "GET",
                payload={},
                headers=headers,
            )
            return {"text": result.text, "ok": result.ok}

    def register_sell_return(self, payload):
        if self.mode == "checkbox_kassa":
            old_payload = payload
            payload = {
                "discounts": old_payload.get("discounts", []),
                "payments": old_payload.get("payments", []),
                "goods": [],
            }
            if old_payload.get("delivery"):
                payload["delivery"] = old_payload["delivery"]
            if old_payload.get("related_receipt_id"):
                payload["related_receipt_id"] = old_payload["related_receipt_id"]
            goods = old_payload.get("goods", [])
            for good in goods:
                payload["goods"].append(
                    {
                        "code": good["good"]["code"],
                        "name": good["good"]["name"],
                        "price": good["good"]["price"],
                        "barcode": good["good"]["barcode"],
                        "quantity": good["quantity"],
                        "taxes": good["good"]["tax"],
                        "is_return": good.get("is_return", False),
                        "discounts": good.get("discounts", []),
                    }
                )

            endpoint = "/api/v1/receipt/sell"
            headers = {}
        else:
            endpoint = "/api/v1/receipts/sell"
            headers = {
                "Authorization": "Bearer " + self.access_token,
            }

        result = self.send_request(
            endpoint,
            "POST",
            payload=payload,
            headers=headers,
        )
        return result

    def get_receipt_info(self, receipt_id, rep_type):
        endpoint = f"/api/v1/receipts/{receipt_id}/{rep_type}"
        result = self.send_request(
            endpoint,
            "GET",
            payload={},
        )
        return result
