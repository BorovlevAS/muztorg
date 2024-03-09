# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class SaleReturnCancel(models.TransientModel):
    _name = "sale.return.cancel"
    _description = "Return Order Cancel"

    order_id = fields.Many2one(
        "sale.stock.return", string="Return Order", required=True, ondelete="cascade"
    )

    def action_cancel(self):
        return self.order_id.with_context(
            disable_cancel_warning=True
        ).action_set_cancel()
