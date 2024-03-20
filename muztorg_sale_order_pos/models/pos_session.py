from odoo import _, fields, models


class PosSessionPaymentLine(models.Model):
    _name = "pos.session.payment.data"

    pos_session_id = fields.Many2one(
        comodel_name="pos.session",
        string="POS Session (nnt)",
    )

    currency_id = fields.Many2one(
        comodel_name="res.currency",
        related="pos_session_id.cash_register_id.currency_id",
        string="Currency (nnt)",
    )
    name = fields.Char(string="Payment type", size=64)
    amount = fields.Monetary(string="Amount")

    def get_line_data(self):
        self.ensure_one()
        lang = self.env["res.lang"].search([("code", "=", self.env.lang)])
        amount_str = lang.format(
            "%.{}f".format(self.currency_id.decimal_places), self.amount, True, True
        )
        if self.currency_id.position == "after":
            amount_str += " " + self.currency_id.symbol
        else:
            amount_str = self.currency_id.symbol + " " + amount_str
        return {
            "name": self.name,
            "amount": amount_str,
            "currency_id": self.currency_id.id,
        }


class PosSession(models.Model):
    _inherit = "pos.session"

    return_order_counter = fields.Integer(
        string="RO count", compute="_compute_return_order_counter"
    )

    pos_payment_lines = fields.One2many(
        comodel_name="pos.session.payment.data",
        inverse_name="pos_session_id",
        compute="_compute_pos_payment_lines",
        string="Payment Lines",
    )

    def _compute_return_order_counter(self):
        for record in self:
            record.return_order_counter = self.env["sale.stock.return"].search_count(
                [("pos_session_id", "=", record.id)]
            )

    def _compute_pos_payment_lines(self):
        for session in self:
            sale_orders = self.env["sale.order"].search(
                [("pos_session_id", "=", session.id)]
            )
            return_orders = self.env["sale.stock.return"].search(
                [("pos_session_id", "=", session.id)]
            )
            payment_lines = {
                _("Balance start in CASH"): session.cash_register_balance_start,
                _("Cash transactions"): session.cash_register_total_entry_encoding,
                _("Balance end in CASH"): session.cash_register_balance_end,
            }
            sale_order_pos_line_ids = sale_orders.mapped("sale_order_pos_line_ids")
            for line in sale_order_pos_line_ids:
                label_name = (
                    line.payment_type.checkbox_payment_label
                    or line.payment_type.checkbox_payment_type
                )
                if label_name == "CASH":
                    continue
                if label_name == "CASHLESS":
                    label_name = _("CARD")
                if label_name not in payment_lines:
                    payment_lines[label_name] = 0
                payment_lines[label_name] += line.payment_amount

            return_order_pos_line_ids = return_orders.mapped(
                "return_order_pos_line_ids"
            )

            for line in return_order_pos_line_ids:
                label_name = (
                    line.payment_type.checkbox_payment_label
                    or line.payment_type.checkbox_payment_type
                )
                if label_name == "CASH":
                    continue
                if label_name == "CASHLESS":
                    label_name = _("CARD")
                if label_name not in payment_lines:
                    payment_lines[label_name] = 0
                payment_lines[label_name] -= line.payment_amount

            new_vals = []

            for key, value in payment_lines.items():
                new_vals.append(
                    self.env["pos.session.payment.data"].create(
                        {
                            "pos_session_id": session.id,
                            "name": key,
                            "amount": value,
                        }
                    )
                )

            session.pos_payment_lines = [(6, 0, [x.id for x in new_vals])]

    def get_related_return_orders(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "simbioz_sale_order_return.sale_stock_return_action"
        )
        action["domain"] = [("pos_session_id", "=", self.id)]
        return action

    def action_print_x_report(self):
        response = self._checkbox_xreport()

        if not response["ok"]:
            return False

        report_text = response["text"]

        wizard = self.env["xreport.wizard"].create(
            {
                "report_data": report_text,
            }
        )

        view = self.env.ref("muztorg_sale_order_pos.xreport_wizard_view_form")

        return {
            "name": _("X-Report"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "xreport.wizard",
            "views": [(view.id, "form")],
            "view_id": view.id,
            "target": "new",
            "res_id": wizard.id,
        }

    def action_pos_session_closing_control(self):
        res = super().action_pos_session_closing_control()
        for session in self:
            if session.use_checkbox and session.config_id.cash_control:
                if session.cash_register_id:
                    session.cash_register_id.write(
                        {
                            "balance_end_real": session.cash_register_balance_end,
                        }
                    )
                session._compute_cash_balance()
                session.action_pos_session_close()

        return res
