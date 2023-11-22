from odoo import api, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.model_create_multi
    def create(self, vals_list):
        result = super().create(vals_list)

        for order in result:
            if (
                not order.workflow_process_id
                and order.company_id.biko_default_sale_workflow_id
            ):
                order.update(
                    {
                        "workflow_process_id": order.company_id.biko_default_sale_workflow_id.id,
                    }
                )

        return result
