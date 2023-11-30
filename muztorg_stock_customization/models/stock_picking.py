from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    biko_reason_return = fields.Char(
        "Reason for return",
    )
