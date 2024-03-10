from odoo import _, fields, models, tools
from odoo.exceptions import UserError


class SaleStockReturn(models.Model):
    _inherit = "sale.stock.return"

    sale_order_pos_line_ids = fields.One2many(
        comodel_name="sale.order.pos.line",
        related="sale_order_id.sale_order_pos_line_ids",
        string="Sale Order Pos Lines",
    )

    is_fiscal_registered = fields.Boolean(
        string="Fiscal Registered (nnt)",
        compute="_compute_is_fiscal_registered",
    )

    # fiscal rec. required if fiscal registered for returned order
    fiscal_receipt_req = fields.Boolean(
        related="sale_order_id.is_fiscal_registered",
        string="Fiscal Receipt Required (nnt)",
    )

    checkbox_receipt_id = fields.Char(string="Checkbox receipt id", copy=False)
    checkbox_receipt_response = fields.Text(
        string="Checkbox_receipt_response", copy=False
    )
    checkbox_receipt_qr_code = fields.Binary(
        string="Receipt QR code", attachment=True, copy=False
    )
    checkbox_receipt_html = fields.Html(string="Receipt HTML", copy=False)
    pos_session_id = fields.Many2one(comodel_name="pos.session", string="Session")
    pos_config_id = fields.Many2one(
        related="pos_session_id.config_id", string="POS Config"
    )

    return_order_pos_line_ids = fields.One2many(
        comodel_name="return.order.pos.line",
        inverse_name="order_id",
        string="Pos Lines",
    )

    def _compute_is_fiscal_registered(self):
        for order in self:
            order.is_fiscal_registered = order.checkbox_receipt_id

    def action_open_receipt_wizard(self):
        self.ensure_one()
        view = self.env.ref(
            "muztorg_sale_order_pos.view_return_order_checkbox_wizard_form"
        )

        create_values = {
            "order_id": self.id,
            "mobile_num": self.partner_id.mobile,
        }

        pos_config_ids = self.env["pos.config"].get_pos_config(self.env.uid)
        if pos_config_ids:
            create_values.update(
                {
                    "config_id": pos_config_ids[0].id,
                    "available_pos_config_ids": pos_config_ids._ids,
                }
            )

        precision_rounding = self.currency_id.rounding
        payment_amount_total = tools.float_round(
            sum(self.sale_order_pos_line_ids.mapped("payment_amount")),
            precision_rounding=precision_rounding,
        )
        coef = (
            self.amount_total / payment_amount_total if payment_amount_total != 0 else 0
        )
        if coef == 0:
            return False

        new_lines = []
        sum_total = 0
        max_sum = 0
        max_line = 0

        for payment_line in self.sale_order_pos_line_ids.filtered(
            lambda line: line.payment_amount > 0
        ):
            return_sum = tools.float_round(
                payment_line.payment_amount * coef,
                precision_rounding=precision_rounding,
            )
            sum_total += return_sum

            new_line = {
                "payment_type": payment_line.payment_type.id,
                "payment_amount": return_sum,
            }
            new_lines.append((0, 0, new_line))

            if payment_line.payment_amount > max_sum:
                max_sum = payment_line.payment_amount
                max_line = len(new_lines) - 1

        if not tools.float_is_zero(
            tools.float_round(
                self.amount_total - sum_total, precision_rounding=precision_rounding
            ),
            precision_rounding=precision_rounding,
        ):
            new_lines[max_line][2]["payment_amount"] += tools.float_round(
                self.amount_total - sum_total, precision_rounding=precision_rounding
            )

        create_values.update({"payment_lines": new_lines})

        wizard = self.env["return.order.checkbox.wizard"].create(create_values)

        action = {
            "name": _("Send Receipt to the Checkbox"),
            "type": "ir.actions.act_window",
            "res_model": "return.order.checkbox.wizard",
            "view_mode": "form",
            "view_id": view.id,
            "target": "new",
            "res_id": wizard.id,
        }

        return action

    def action_set_cancel(self):
        if any(self.filtered(lambda order: order.is_fiscal_registered)):
            raise UserError(_("You can't cancel an order with a fiscal receipt."))
        return super().action_set_cancel()
