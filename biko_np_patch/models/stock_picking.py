from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    cost = fields.Float(string="Cost")
    np_shipping_weight = fields.Float(string="Shipping Weight")
    np_shipping_volume = fields.Float(string="Shipping Volume")
    comment = fields.Text(related="sale_id.note", string="Comment")
