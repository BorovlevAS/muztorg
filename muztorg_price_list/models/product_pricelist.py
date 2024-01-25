from odoo import _, api, fields, models

# from datetime import date


class Pricelist(models.Model):
    _inherit = "product.pricelist"

    def import_file_call(self):
        self.ensure_one()
        vals = {"price_id": self.id}
        pl_import = self.env["price.list.import"].create(vals)

        return {
            "name": _("Attachments"),
            "res_model": "price.list.import",
            "res_id": pl_import.id,
            "type": "ir.actions.act_window",
            "view_id": False,
            "view_mode": "form",
            "view_type": "form",
            "target": "new",
        }

    def remove_old_discount_prices(self):
        self.ensure_one()
        date = fields.Datetime.today()
        for line in self.item_ids:
            if line.date_end and line.date_end < date:
                line.unlink()
        return {
            "type": "ir.actions.client",
            "tag": "reload",
        }

    def add_all_product(self):
        PricelistItem = self.env["product.pricelist.item"]
        for price in self:
            if price in self.env.company.biko_price_USD_ids:
                product_ids = self.env["product.template"].search([])
                # [("categ_id", "=", record.id), ("attribute_set_id", "=", False)]
                for prod in product_ids:
                    # item_line = price.item_ids.filtered(
                    #     lambda x: x.product_tmpl_id.id == prod.id
                    # )
                    item_line = price.item_ids.filtered(
                        lambda x, prod=prod: x.product_tmpl_id.id == prod.id
                    )
                    if len(item_line) == 0:
                        vals = {
                            "applied_on": "1_product",
                            "compute_price": "fixed",
                            "pricelist_id": price.id,
                            "base": "list_price",
                        }
                        vals["product_tmpl_id"] = prod.id
                        # if single_line_data["date1"]:
                        #     vals["date_start"] = single_line_data["date1"]
                        # if single_line_data["date2"]:
                        #     vals["date_end"] = single_line_data["date2"]
                        # vals["fixed_price"] = single_line_data["price"]
                        PricelistItem.create(vals)
        return {
            "type": "ir.actions.client",
            "tag": "reload",
        }

    # тут на будущее, если надо будет скріть кнопку
    def can_add_all_product(self):
        can_add = True
        if self.env.company.biko_price_USD_ids:
            for price in self:
                can_add = can_add and (price in self.env.company.biko_price_USD_ids)
        else:
            can_add = False
        return can_add

    @api.model_create_multi
    def _delete_no_active_product(self):
        if self.env.company.biko_price_USD_ids:
            # PricelistItem = self.env["product.pricelist.item"]
            for price in self.env.company.biko_price_USD_ids:
                item_line = price.item_ids.filtered(
                    lambda x: not x.product_tmpl_id.active
                )
                for line in item_line:
                    line.unlink()

    def open_pricelist_rules(self):
        self.ensure_one()
        domain = [
            # "|",
            # ("product_tmpl_id", "=", self.id),
            # ("product_id", "in", self.product_variant_ids.ids),
            ("pricelist_id", "=", self.id),
        ]
        return {
            "name": _("Price Rules"),
            "view_mode": "tree,form",
            "views": [
                (
                    self.env.ref(
                        "muztorg_price_list.biko_product_pricelist_item_tree_view_from_pricelist"
                    ).id,
                    "tree",
                ),
                (False, "form"),
            ],
            "res_model": "product.pricelist.item",
            "type": "ir.actions.act_window",
            "target": "current",
            "domain": domain,
            "context": {
                # "default_product_tmpl_id": self.id,
                "default_pricelist_id": self.id,
                "default_applied_on": "1_product",
                "default_compute_price": "fixed",
                "default_base": "list_price",
                "product_without_variants": True,
            },
        }
