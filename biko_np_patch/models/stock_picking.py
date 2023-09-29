from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class StockPicking(models.Model):
    _name = "stock.picking"
    _inherit = ["stock.picking", "phone.validation.mixin"]

    cost = fields.Float(string="Cost")
    np_shipping_weight = fields.Float(string="Shipping Weight")
    np_shipping_volume = fields.Float(string="Shipping Volume", digits=(10, 4))
    np_length = fields.Integer(
        string="Length (cm)",
        help="The cargo length (cm)",
    )
    np_width = fields.Integer(
        string="Width (cm)",
        help="The cargo width (cm)",
    )
    np_height = fields.Integer(
        string="Height (cm)",
        help="The cargo height (cm)",
    )
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

    biko_dropshipping = fields.Boolean(string="Dropshipping")

    biko_carrier_id = fields.Many2one(
        "delivery.carrier",
        string="Delivery carrier",
        # store=True,
        readonly=True,
        related="sale_id.carrier_id",
    )

    def _inverse_biko_recipient_id(self):
        for stock in self:
            if stock.sale_id:
                sale_order = stock.sale_id
                sale_order.update({"biko_recipient_id": stock.biko_recipient_id})

    @api.onchange("biko_recipient_mobile")
    def _onchange_phone_validation(self):
        if self.biko_recipient_mobile:
            self.biko_recipient_mobile = self.phone_format(self.biko_recipient_mobile)

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
