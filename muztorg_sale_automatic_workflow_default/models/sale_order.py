from odoo import api, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("company_id", False) and not vals.get(
                "workflow_process_id", False
            ):
                company = self.env["res.company"].browse(vals.get("company_id"))
                vals["workflow_process_id"] = (
                    company.biko_default_sale_workflow_id.id or False
                )

        return super().create(vals_list)
