import logging

import pytz

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class PosConfig(models.Model):
    _inherit = "pos.config"

    is_auto_open_pos = fields.Boolean(
        string="Auto Open POS interface",
        default=False,
    )

    is_use_with_sale_order = fields.Boolean(
        string="Use with Sale Order",
        default=False,
    )

    department_ids = fields.Many2many(
        comodel_name="hr.department",
        string="Departments",
    )

    autoclose_session = fields.Boolean(
        string="Autoclose Session",
        default=False,
    )

    autoclose_session_time_string = fields.Char(string="Autoclose Session Time")
    autoclose_session_time = fields.Datetime(
        string="Autoclose Session Time (nnt)",
        compute="_compute_autoclose_session_time",
        store=True,
    )

    @api.depends("autoclose_session_time_string")
    def _compute_autoclose_session_time(self):
        for record in self:
            if not record.autoclose_session_time_string:
                continue

            date_time = fields.Datetime.to_datetime(
                "2020-01-01 {}".format(
                    record.autoclose_session_time_string.replace(" ", "")
                )
            )
            tz_name = record._context.get("tz") or record.env.user.tz
            if tz_name:
                try:
                    timezone = pytz.timezone(tz_name)
                    tz_date = timezone.localize(date_time, is_dst=False)
                    autoclose_session_time = tz_date.astimezone(pytz.UTC)
                    date_time = autoclose_session_time.replace(tzinfo=None)
                except Exception:
                    _logger.debug(
                        "failed to compute context/client-specific timestamp, "
                        "using the UTC value",
                        exc_info=True,
                    )

            record.autoclose_session_time = date_time

    @api.model
    def get_pos_config(self, department_id):
        pos_config_ids = self.search(
            [
                ("is_use_with_sale_order", "=", True),
                ("department_ids", "in", department_id),
            ]
        )
        return pos_config_ids

    def cron_autoclose_session(self):
        for record in self.search([]):
            if record.autoclose_session:
                if record.autoclose_session_time:
                    now = fields.Datetime.now()

                    now_hour, now_min = now.hour, now.minute

                    ac_hour, ac_min = (
                        record.autoclose_session_time.hour,
                        record.autoclose_session_time.minute,
                    )

                    if now_hour >= ac_hour and now_min >= ac_min:
                        opened_sessions = record.session_ids.filtered(
                            lambda s: not s.state == "closed"
                        )
                        for session in opened_sessions:
                            session.action_pos_session_closing_control()
        return True

    def open_session_cb(self, check_coa=True):
        """new session button

        create one if none exist
        access cash control interface if enabled or start a session
        """
        self.ensure_one()
        if not self.current_session_id:
            self._check_pricelists()
            self._check_company_journal()
            self._check_company_invoice_journal()
            self._check_company_payment()
            self._check_currencies()
            self._check_profit_loss_cash_journal()
            self._check_payment_method_ids()
            self._check_payment_method_receivable_accounts()
            self.env["pos.session"].create(
                {"user_id": self.env.uid, "config_id": self.id}
            )

        if self.is_auto_open_pos:
            return self.open_ui()

        return True
