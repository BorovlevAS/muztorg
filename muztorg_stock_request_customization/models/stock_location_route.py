from odoo import fields, models


class StockLocationRoute(models.Model):
    _inherit = "stock.location.route"

    stock_request_selectable = fields.Boolean(
        "Applicable on Stock Request",
        #   default=True,
        help="When checked, the route will be selectable in the Stock Request form.",
    )
