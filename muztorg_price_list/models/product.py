from odoo import api, fields, models


class Product(models.Model):
    _inherit = "product.template"

    biko_mg_id = fields.Many2one(
        string="Product marketing group",
        comodel_name="biko.marketing.group",
        # compute="_compute_biko_mg_id",
        # store=False,
    )

    # def _compute_biko_mg_id(self):

    #     for rec in self:
    #         date = fields.Date.today()
    #         retail_price = self.env.company.biko_price_retail._compute_price_rule(
    #             [(rec, 1, False)], date, rec.uom_id.id
    #         )[rec.id][0]
    #         dealer_price = self.env.company.biko_price_dealer._compute_price_rule(
    #             [(rec, 1, False)], date, rec.uom_id.id
    #         )[rec.id][
    #             0
    #         ]  # TDE: 0 = price, 1 = rule

    #         # rec.biko_mg_id = False
    #         if dealer_price != 0:
    #             percent = (retail_price - dealer_price) / retail_price * 100
    #             mg = self.env["biko.marketing.group"].search(
    #                 [("limit_from", "<=", percent), ("limit_to", ">", percent)], limit=1
    #             )
    #             if mg:
    #                 rec.biko_mg_id = mg
    #             else:
    #                 rec.biko_mg_id = False
    #         else:
    #             rec.biko_mg_id = False

    def calculate_marketing_group(self):
        date = fields.Date.today()

        retail_price = self.env.company.biko_price_retail._compute_price_rule(
            [(self, 1, False)], date, self.uom_id.id
        )[self.id][0]
        dealer_price = self.env.company.biko_price_dealer._compute_price_rule(
            [(self, 1, False)], date, self.uom_id.id
        )[self.id][0]

        mg_defolt = self.env["biko.marketing.group"].search(
            [("limit_from", "<=", 5), ("limit_to", ">", 0)], limit=1
        )
        if (
            not retail_price
            or retail_price == 0
            or not dealer_price
            or dealer_price == 0
        ):
            vals = {
                "biko_mg_id": mg_defolt,
            }
            self.write(vals)
        elif retail_price != 0:
            percent = (retail_price - dealer_price) / retail_price * 100
            mg = self.env["biko.marketing.group"].search(
                [("limit_from", "<=", percent), ("limit_to", ">", percent)], limit=1
            )
            if mg and self.biko_mg_id != mg:
                vals = {
                    "biko_mg_id": mg,
                }
                self.write(vals)

        return True

    @api.model_create_multi
    def _update_biko_mg_id(self):
        if self.env.company.biko_price_dealer and self.env.company.biko_price_retail:
            products_item = self.env["product.pricelist.item"].search(
                [
                    (
                        "pricelist_id",
                        "in",
                        (
                            self.env.company.biko_price_dealer.id,
                            self.env.company.biko_price_retail.id,
                        ),
                    ),
                    ("applied_on", "=", "1_product"),
                    ("compute_price", "=", "fixed"),
                    ("base", "=", "list_price"),
                ]
            )
            products = []
            for item in products_item:
                if item.product_tmpl_id not in products:
                    item.product_tmpl_id.calculate_marketing_group()
                    products.append(item.product_tmpl_id)

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for record in res:
            record.add_product_in_price()
        return res

    def add_product_in_price(self):
        self.ensure_one()
        if self.env.company.biko_price_USD_ids:
            PricelistItem = self.env["product.pricelist.item"]
            for price in self.env.company.biko_price_USD_ids:
                item_line = price.item_ids.filtered(
                    lambda x: x.product_tmpl_id.id == self.id
                )
                if len(item_line) == 0:
                    vals = {
                        "applied_on": "1_product",
                        "compute_price": "fixed",
                        "pricelist_id": price.id,
                        "base": "list_price",
                    }
                    vals["product_tmpl_id"] = self.id
                    PricelistItem.create(vals)
