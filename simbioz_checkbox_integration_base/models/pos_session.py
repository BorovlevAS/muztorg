import logging

from odoo import _, api, exceptions, fields, models

from . import checkbox_api as API

_logger = logging.getLogger(__name__)


class PosSession(models.Model):
    _inherit = "pos.session"

    checkbox_url = fields.Char(related="config_id.checkbox_url")
    checkbox_port = fields.Integer(related="config_id.checkbox_port")
    checkbox_mode = fields.Selection(related="config_id.checkbox_mode")
    checkbox_license_key = fields.Char(related="config_id.checkbox_license_key")

    def _checkbox_cashier_signin(self):
        self.ensure_one()

        checkbox_api = API.CheckboxAPI(
            api_url=self.checkbox_url,
            api_port=self.checkbox_port,
            cb_license=self.checkbox_license_key,
            mode=self.checkbox_mode,
            access_token=self.checkbox_access_token,
        )

        r = checkbox_api.cashier_signin(
            self.config_id.checkbox_cashier_login,
            self.config_id.checkbox_cashier_password,
        )

        _logger.debug("_checkbox_cashier_signin: response: %s", r["text"])
        if r["ok"]:
            access_token = r["access_token"]
            self.update(
                {
                    "checkbox_access_token": access_token,
                    "checkbox_is_signin": True,
                }
            )
        else:
            raise exceptions.Warning(
                _("Signin error: {error_msg}").format(error_msg=r["text"])
            )

    def _checkbox_shift_create(self):
        self.ensure_one()

        checkbox_api = API.CheckboxAPI(
            api_url=self.checkbox_url,
            api_port=self.checkbox_port,
            cb_license=self.checkbox_license_key,
            mode=self.checkbox_mode,
            access_token=self.checkbox_access_token,
        )

        r = checkbox_api.shift_create()
        _logger.debug("_checkbox_shift_create: response: %s", r["text"])
        if not r["ok"]:
            raise exceptions.Warning(r["text"])

    def action_pos_session_closing_control(self):
        res = super().action_pos_session_closing_control()
        for session in self.filtered(lambda s: s.use_checkbox):
            try:
                session._checkbox_shift_close()
                session._checkbox_cashier_signout()
                session.message_post(
                    body=_("Checkbox shift closed and cashier signed out"),
                    author_id=1,
                )
            except exceptions.Warning as e:
                session.message_post(
                    body=_(
                        "Session closed but checkbox shift wasn't closed. Error: %(cb_error)s",
                        cb_error=e,
                    ),
                    author_id=1,
                )

        return res

    def _checkbox_cashier_signout(self):
        self.ensure_one()
        if self.checkbox_access_token:
            checkbox_api = API.CheckboxAPI(
                api_url=self.checkbox_url,
                api_port=self.checkbox_port,
                cb_license=self.checkbox_license_key,
                mode=self.checkbox_mode,
                access_token=self.checkbox_access_token,
            )
            r = checkbox_api.cashier_signout()
            _logger.debug("_checkbox_cashier_signout: response: %s", r["text"])

            if r["ok"]:
                self.update(
                    {
                        "checkbox_access_token": False,
                        "checkbox_is_signin": False,
                    }
                )
            else:
                raise exceptions.Warning(
                    _("Signout error: {error_msg}").format(error_msg=r["text"])
                )

    def _checkbox_shift_close(self):
        self.ensure_one()

        checkbox_api = API.CheckboxAPI(
            api_url=self.checkbox_url,
            api_port=self.checkbox_port,
            cb_license=self.checkbox_license_key,
            mode=self.checkbox_mode,
            access_token=self.checkbox_access_token,
        )

        r = checkbox_api.shift_close()
        _logger.debug("_checkbox_shift_close: response: %s", r["text"])
        if not r["ok"]:
            raise exceptions.Warning(r["text"])

    def _checkbox_service(self, amount):
        self.ensure_one()

        checkbox_api = API.CheckboxAPI(
            api_url=self.checkbox_url,
            api_port=self.checkbox_port,
            cb_license=self.checkbox_license_key,
            mode=self.checkbox_mode,
            access_token=self.checkbox_access_token,
        )
        result = checkbox_api.service_receipt(amount)

        if not result["ok"]:
            raise exceptions.Warning(result["text"])

    def _checkbox_xreport(self):
        self.ensure_one()

        checkbox_api = API.CheckboxAPI(
            api_url=self.checkbox_url,
            api_port=self.checkbox_port,
            cb_license=self.checkbox_license_key,
            mode=self.checkbox_mode,
            access_token=self.checkbox_access_token,
        )
        result = checkbox_api.reports_xreport()

        if not result["ok"]:
            raise exceptions.Warning(result["text"])

        return result

    def _checkbox_register_sell_return(self, payload):
        self.ensure_one()

        checkbox_api = API.CheckboxAPI(
            api_url=self.checkbox_url,
            api_port=self.checkbox_port,
            cb_license=self.checkbox_license_key,
            mode=self.checkbox_mode,
            access_token=self.checkbox_access_token,
        )
        result = checkbox_api.register_sell_return(payload)

        return result

    @api.model
    def _checkbox_get_receipt_info(self, receipt_id, rep_type):
        checkbox_api = API.CheckboxAPI(  # nosec B106
            api_url="https://api.checkbox.in.ua",
            api_port=0,
            cb_license="",
            mode="",
            access_token="",
        )
        result = checkbox_api.get_receipt_info(receipt_id, rep_type)

        return result
