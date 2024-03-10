from odoo import fields, models


class SaleOrderPosLines(models.Model):
    _name = "return.order.pos.line"

    order_id = fields.Many2one(comodel_name="sale.stock.return", string="Order (nnt)")

    payment_type = fields.Many2one(
        comodel_name="so.payment.type",
        string="Payment Type",
    )

    pos_payment_method_id = fields.Many2one(
        comodel_name="pos.payment.method",
        string="(POS) Payment Method",
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        related="order_id.currency_id",
        string="Currency (nnt)",
    )
    payment_amount = fields.Monetary(string="Payment Amount")
