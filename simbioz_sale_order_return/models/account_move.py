from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    sale_stock_return_id = fields.Many2one(
        comodel_name="sale.stock.return",
        string="Sale stock return (nnt)",
        ondelete="restrict",
    )
