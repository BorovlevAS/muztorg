from odoo import api, models


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.model
    def action_delete_all_am(self):
        SaleOrder = self.env["sale.order"].sudo()
        AccountMove = self.env["account.move"].sudo()

        SaleOrder.search([("workflow_process_id", "!=", False)]).write(
            {"workflow_process_id": False}
        )
        am = AccountMove.search([])
        am.button_draft()
        am.with_context(force_delete=True).unlink()
        return True
