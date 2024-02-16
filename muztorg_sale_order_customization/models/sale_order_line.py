from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    json_remainings_popover = fields.Char(
        related="product_id.json_remainings_popover", readonly=True
    )

    margin = fields.Float(
        groups="muztorg_sale_order_customization.biko_group_show_margin"
    )
    margin_percent = fields.Float(
        groups="muztorg_sale_order_customization.biko_group_show_margin"
    )
    purchase_price = fields.Float(
        groups="muztorg_sale_order_customization.biko_group_show_margin"
    )

    uktzed_id = fields.Many2one(comodel_name="catalog.uktzed", string="UKTZED", related="product_id.uktzed_id")

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
        result = super().create(vals_list)

        for record in result:
            order_id = record.order_id

            if not order_id:
                continue
            if not order_id.biko_1c_currency:
                continue

            company_id = order_id.company_id
            pricelist_uah = company_id.biko_uah_pricelist_id
            from_curr = self.env["res.currency"].search(
                [("id", "=", order_id.biko_1c_currency)]
            )

            if not from_curr:
                continue

            to_curr = pricelist_uah.currency_id

            if from_curr == to_curr:
                continue

            price_unit = from_curr._convert(
                record["price_unit"],
                to_curr,
                company_id,
                order_id.date_order,
            )
            record.write({"price_unit": price_unit})

        return result
