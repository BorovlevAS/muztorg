from odoo import api, models
from odoo.osv import expression


class AccountReconciliation(models.AbstractModel):
    _inherit = "account.reconciliation.widget"

    @api.model
    def _get_statement_line(self, st_line):
        result = super()._get_statement_line(st_line)
        result.update({"payment_ref": st_line.payment_ref})

        return result

    def _str_domain_for_mv_line(self, search_str):
        result = super()._str_domain_for_mv_line(search_str)
        orders = self.env["sale.order"].search(
            [
                "|",
                ("biko_website_ref", "ilike", search_str),
                ("biko_1c_ref", "ilike", search_str),
            ]
        )
        if orders:
            move_ids = orders.mapped("invoice_ids")._ids
            result = expression.OR([result, [("move_id.id", "in", move_ids)]])

        return result
