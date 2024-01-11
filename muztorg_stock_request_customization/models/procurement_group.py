from odoo import fields, models


class ProcurementGroup(models.Model):
    _inherit = "procurement.group"

    stock_request_order_id = fields.Many2one(
        "stock.request.order", "Stock Request Order"
    )
