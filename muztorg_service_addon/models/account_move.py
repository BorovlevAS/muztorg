from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.model
    def action_delete_all_am(self):
        date_to = fields.Datetime.to_datetime("2024-01-01")
        SaleOrder = self.env["sale.order"].sudo()
        AccountMove = self.env["account.move"].sudo()

        orders = SaleOrder.search(
            [
                ("workflow_process_id", "!=", False),
                ("date_order", "<", date_to),
            ]
        )
        orders.write({"workflow_process_id": False})

        # customer invoices
        am = AccountMove.search([("date", "<", date_to)])
        am.button_draft()
        am.with_context(force_delete=True).unlink()
        return True
