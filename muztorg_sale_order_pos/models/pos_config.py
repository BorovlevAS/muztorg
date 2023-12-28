from odoo import api, fields, models


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

    @api.model
    def get_pos_config(self, department_id):
        pos_config_ids = self.search(
            [
                ("is_use_with_sale_order", "=", True),
                ("department_ids", "in", department_id),
            ]
        )
        return pos_config_ids

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
