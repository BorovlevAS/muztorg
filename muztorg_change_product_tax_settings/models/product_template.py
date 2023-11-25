from odoo import api, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.model
    def action_clear_taxes(self):
        products = self.env["product.template"].search([("type", "=", "product")])
        products.with_context(no_rename=True).write(
            {
                "taxes_id": [(5, 0, 0)],
                "supplier_taxes_id": [(5, 0, 0)],
            }
        )
