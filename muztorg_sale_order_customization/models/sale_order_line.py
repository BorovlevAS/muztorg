from odoo import api, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _calculate_customer_lead(self, vals):
        customer_lead = vals.get("customer_lead", 0)
        product_id = vals.get("product_id", False)
        if product_id:
            product_id = self.env["product.product"].browse(product_id)
        if not customer_lead and product_id and product_id.sale_delay:
            vals.update({"customer_lead": product_id.sale_delay})

    def write(self, vals):
        self._calculate_customer_lead(vals)
        return super().write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._calculate_customer_lead(vals)
        return super().create(vals_list)
