from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    cost = fields.Float(string="Cost")
    np_shipping_weight = fields.Float(string="Shipping Weight")
    np_shipping_volume = fields.Float(string="Shipping Volume", digits=(10, 4))
    comment = fields.Text(related="sale_id.note", string="Comment")
    afterpayment_check = fields.Boolean(string="Afterpayment check", default=False)

    biko_recipient_id = fields.Many2one(
        "res.partner",
        string="Recipient person",
        store=True,
        compute="_compute_biko_recipient_id",
        inverse="_inverse_biko_recipient_id",
    )
    biko_recipient_mobile = fields.Char(
        string="Mobile",
        related="biko_recipient_id.mobile",
        readonly=False,
    )

    biko_1c_phone = fields.Char(
        string="1C phone",
        related="biko_recipient_id.biko_1c_phone",
    )

    def _inverse_biko_recipient_id(self):
        for stock in self:
            if stock.sale_id:
                sale_order = stock.sale_id
                sale_order.update({"biko_recipient_id": stock.biko_recipient_id})

    @api.depends("sale_id")
    def _compute_biko_recipient_id(self):
        for stock in self:
            stock.update({"biko_recipient_id": stock.sale_id.biko_recipient_id})

    @api.constrains("afterpayment_check", "backward_money")
    def _check_backward(self):
        for data in self:
            if data.backward_money and data.afterpayment_check:
                raise ValidationError(
                    _(
                        "You can choose only single option, "
                        '"Backward" or "After payment".'
                    )
                )
