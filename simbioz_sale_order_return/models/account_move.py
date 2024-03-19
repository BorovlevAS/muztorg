from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    sale_stock_return_id = fields.Many2one(
        comodel_name="sale.stock.return",
        string="Sale stock return (nnt)",
        ondelete="restrict",
    )


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    stock_return_line_id = fields.Many2one(
        comodel_name="sale.stock.return.line",
        string="Stock Return Line (nnt)",
        ondelete="restrict",
        index=True,
    )
