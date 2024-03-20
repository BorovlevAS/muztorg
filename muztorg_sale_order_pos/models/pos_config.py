import json
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

    user_ids = fields.Many2many(
        comodel_name="res.users",
        string="Users",
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

    payment_corr_ids = fields.One2many(
        comodel_name="sale.pos.payment.line",
        inverse_name="pos_config_id",
        string="Payment Types Correspondence",
    )

    cash_register_total_entry_encoding = fields.Monetary(
        related="current_session_id.cash_register_total_entry_encoding",
        string="Total Cash Transaction",
        readonly=True,
        help="Total of all paid sales orders",
    )

    cash_register_balance_end = fields.Monetary(
        related="current_session_id.cash_register_balance_end",
        string="Theoretical Closing Balance",
        help="Sum of opening balance and transactions.",
        readonly=True,
    )
    pos_payment_lines = fields.One2many(related="current_session_id.pos_payment_lines")
    pos_payment_lines_json = fields.Text(compute="_compute_pos_payment_lines_json")

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

    def _compute_pos_payment_lines_json(self):
        for record in self:
            pos_payment_lines = record.pos_payment_lines
            pos_payment_lines_json = []
            for line in pos_payment_lines:
                pos_payment_lines_json.append(line.get_line_data())
            record.pos_payment_lines_json = json.dumps(pos_payment_lines_json)

    @api.model
    def get_pos_config(self, user_id):
        pos_config_ids = self.search(
            [
                ("is_use_with_sale_order", "=", True),
                ("user_ids", "in", user_id),
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
            pos_session = self.env["pos.session"].create(
                {
                    "user_id": self.env.uid,
                    "config_id": self.id,
                }
            )
            pos_session.state = "opened"

        if self.is_auto_open_pos:
            return self.open_ui()

        return True
