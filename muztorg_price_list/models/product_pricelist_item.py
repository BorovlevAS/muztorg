from odoo import api, fields, models, tools


class PricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    biko_is_special_rounding = fields.Boolean("Special rounding")
    biko_price_to = fields.Float("Price up to", digits="Product Price")
    biko_price_to_round = fields.Float(
        "Price Rounding up to",
        digits="Product Price",
        # help="Sets the price so that it is a multiple of this value.\n"
        #      "Rounding is applied after the discount and before the surcharge.\n"
        #      "To have prices that end in 9.99, set rounding 10, surcharge -0.01"
        help="в перерахунку на валюту даного прайс-листа, значення задається вручну,\n"
        "може бути будь-яке або не заповнено",
    )

    biko_product_brand_id = fields.Many2one(
        comodel_name="product.brand",
        string="Brand",
        related="product_tmpl_id.product_brand_id",
        store=True,
    )
    biko_categ_id = fields.Many2one(
        string="Category",
        comodel_name="product.category",
        related="product_tmpl_id.categ_id",
        store=True,
    )
    biko_control_code = fields.Char(
        string="Control code",
        related="product_tmpl_id.biko_control_code",
        store=True,
    )

    def _compute_price(self, price, price_uom, product, quantity=1.0, partner=False):
        """Compute the unit price of a product in the context of a pricelist application.
        The unused parameters are there to make the full context available for overrides.
        """

        def convert_to_price_uom(price, product, price_uom):
            return product.uom_id._compute_price(price, price_uom)

        self.ensure_one()
        date = self.env.context.get("date") or fields.Date.today()
        # convert_to_price_uom = lambda price: product.uom_id._compute_price(
        #     price, price_uom
        # )

        if self.compute_price == "fixed":
            price = convert_to_price_uom(self.fixed_price, product, price_uom)
        elif self.compute_price == "percentage":
            price = (price - (price * (self.percent_price / 100))) or 0.0
        else:
            # complete formula
            price_limit = price
            price = (price - (price * (self.price_discount / 100))) or 0.0
            if self.base == "standard_price":
                price_currency = product.cost_currency_id
            elif self.base == "pricelist":
                price_currency = (
                    self.currency_id
                )  # Already converted before to the pricelist currency
            else:
                price_currency = product.currency_id
            if self.biko_is_special_rounding:
                # найдем исходную цену в прайсе
                if not price_uom and self._context.get("uom"):
                    uom_id = self._context["uom"]
                else:
                    uom_id = price_uom.id
                base_price = self.base_pricelist_id._compute_price_rule(
                    [(product, quantity, partner)], date, uom_id
                )[product.id][
                    0
                ]  # TDE: 0 = price, 1 = rule
                if base_price < self.biko_price_to:
                    price = tools.float_round(
                        price, precision_rounding=self.biko_price_to_round
                    )
                elif self.price_round:
                    price = tools.float_round(
                        price, precision_rounding=self.price_round
                    )

            elif self.price_round:
                price = tools.float_round(price, precision_rounding=self.price_round)

            def convert_to_base_price_currency(amount):
                return self.currency_id._convert(
                    amount, price_currency, self.env.company, date, round=False
                )

            if self.price_surcharge:
                price_surcharge = convert_to_base_price_currency(self.price_surcharge)
                price_surcharge = convert_to_price_uom(
                    price_surcharge, product, price_uom
                )
                price += price_surcharge

            if self.price_min_margin:
                price_min_margin = convert_to_base_price_currency(self.price_min_margin)
                price_min_margin = convert_to_price_uom(
                    price_min_margin, product, price_uom
                )
                price = max(price, price_limit + price_min_margin)

            if self.price_max_margin:
                price_max_margin = convert_to_base_price_currency(self.price_max_margin)
                price_max_margin = convert_to_price_uom(
                    price_max_margin, product, price_uom
                )
                price = min(price, price_limit + price_max_margin)
        return price

    def write(self, values):
        res = super().write(values)
        if (
            self.env.company.biko_price_dealer
            and self.env.company.biko_price_retail
            and (
                self.pricelist_id == self.env.company.biko_price_dealer
                or self.pricelist_id == self.env.company.biko_price_retail
            )
        ):
            res.product_tmpl_id.calculate_marketing_group()
        return res

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        if (
            self.env.company.biko_price_dealer
            and self.env.company.biko_price_retail
            and (
                res.pricelist_id == self.env.company.biko_price_dealer
                or res.pricelist_id == self.env.company.biko_price_retail
            )
        ):
            res.product_tmpl_id.calculate_marketing_group()
        return res
