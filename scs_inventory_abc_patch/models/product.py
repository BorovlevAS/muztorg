from odoo import api, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.depends("outgoing_qty", "qty_available", "virtual_available")
    def _compute_sale_count(self):
        all_product = {}
        all_product_sales = 0
        for group in self.env["sale.report"].read_group(
            [("state", "in", ["sale", "done"])],
            ["product_id", "product_uom_qty"],
            ["product_id"],
        ):
            if group["product_id"]:
                all_product[group["product_id"][0]] = group["product_uom_qty"]
        product_list = [key for key in all_product]
        for product in self.env["product.product"].browse(product_list):
            all_product_sales += all_product.get(product.id, 0) * product.standard_price
        r = {}
        domain = [("state", "in", ["sale", "done"]), ("product_id", "in", self.ids)]
        for group in self.env["sale.report"].read_group(
            domain, ["product_id", "product_uom_qty"], ["product_id"]
        ):
            r[group["product_id"][0]] = group["product_uom_qty"]
        for product in self:
            product.sale_persent = 0
            if all_product_sales:
                product.sale_persent = round(
                    100
                    / all_product_sales
                    * (r.get(product.id, 0) * product.standard_price),
                    2,
                )
            product.sale_value = r.get(product.id, 0) * product.standard_price
        return r
