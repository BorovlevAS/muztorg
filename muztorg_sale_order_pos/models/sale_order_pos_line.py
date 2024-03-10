from odoo import fields, models


class SaleOrderPosLines(models.Model):
    _name = "sale.order.pos.line"

    order_id = fields.Many2one(comodel_name="sale.order", string="Order (nnt)")

    payment_type = fields.Many2one(
        comodel_name="so.payment.type",
        string="Payment Type",
    )

    pos_payment_method_id = fields.Many2one(
        comodel_name="pos.payment.method",
        string="(POS) Payment Method",
    )

    payment_amount = fields.Float(string="Payment Amount", digits=(12, 2))
