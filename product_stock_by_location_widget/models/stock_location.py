from odoo import fields, models


class StockLocation(models.Model):
    _inherit = "stock.location"

    show_stock_on_products = fields.Boolean(
        help="If true, this location will be shown on the pop up window opened"
        "from products kanban and tree view"
    )
