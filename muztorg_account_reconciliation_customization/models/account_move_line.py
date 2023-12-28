from odoo import api, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.model_create_multi
    def create(self, vals_list):
        result = super().create(vals_list)
        for line in result:
            if line.move_id and line.move_id.state == "posted":
                line.create_analytic_lines()

        return result
