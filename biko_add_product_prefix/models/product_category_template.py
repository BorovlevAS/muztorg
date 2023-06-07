import re

from odoo import models, fields, api
from odoo.osv import expression


class ProductCategory(models.Model):
    _inherit = "product.category"

    biko_product_prefix_ids = fields.Many2many(string="Prefix", comodel_name="biko.product.prefix")

    @api.model
    def _name_search(self, name, args=None, operator="ilike", limit=100, name_get_uid=None):
        if not args:
            args = []
        if name:
            _prefixes_ids = self.env["biko.product.prefix"].search([("name", operator, name)]).read(["id"])
            _ids_link = [x["id"] for x in _prefixes_ids]
            positive_operators = ["=", "ilike", "=ilike", "like", "=like"]
            category_ids = []
            if operator in positive_operators:
                category_ids = list(
                    self._search(
                        [("biko_product_prefix_ids.id", "in", _ids_link)] + args,
                        limit=limit,
                        access_rights_uid=name_get_uid,
                    )
                )

            if not category_ids and operator not in expression.NEGATIVE_TERM_OPERATORS:
                elements = [el for el in name.rsplit(" ") if el]
                domain = []
                for el in elements:
                    domain.append(("name", operator, el))
                category_ids = list(self._search(args + domain, limit=limit))

            if not category_ids and operator not in expression.NEGATIVE_TERM_OPERATORS:
                # Do not merge the 2 next lines into one single search, SQL search performance would be abysmal
                # on a database with thousands of matching products, due to the huge merge+unique needed for the
                # OR operator (and given the fact that the 'name' lookup results come from the ir.translation table
                # Performing a quick memory merge of ids in Python will give much better performance
                category_ids = list(
                    self._search(
                        args + [("biko_product_prefix_ids.id", "in", _ids_link)],
                        limit=limit,
                    )
                )
                if not limit or len(category_ids) < limit:
                    # we may underrun the limit because of dupes in the results, that's fine
                    limit2 = (limit - len(category_ids)) if limit else False
                    category2_ids = self._search(
                        args + [("name", operator, name), ("id", "not in", category_ids)],
                        limit=limit2,
                        access_rights_uid=name_get_uid,
                    )
                    category_ids.extend(category2_ids)
            elif not category_ids and operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = expression.OR(
                    [
                        [
                            "&",
                            ("biko_product_prefix_ids.id", "in", _ids_link),
                            ("name", operator, name),
                        ],
                        [
                            "&",
                            ("biko_product_prefix_ids", "=", False),
                            ("name", operator, name),
                        ],
                    ]
                )
                domain = expression.AND([args, domain])
                category_ids = list(self._search(domain, limit=limit, access_rights_uid=name_get_uid))
            if not category_ids and operator in positive_operators:
                ptrn = re.compile("(\[(.*?)\])")
                res = ptrn.search(name)
                if res:
                    _prefixes_ids = (
                        self.env["biko.product.prefix"].search([("name", operator, res.group(2))]).read(["id"])
                    )
                    _ids_link = [x["id"] for x in _prefixes_ids]
                    category_ids = list(
                        self._search(
                            [("biko_product_prefix_ids.id", "in", _ids_link)] + args,
                            limit=limit,
                            access_rights_uid=name_get_uid,
                        )
                    )
        else:
            category_ids = self._search(args, limit=limit, access_rights_uid=name_get_uid)
        return category_ids


class ProductTemplate(models.Model):
    _inherit = "product.template"

    biko_avail_prefixes = fields.Many2many(related="categ_id.biko_product_prefix_ids")
    biko_product_prefix = fields.Many2one(
        string="Prefix",
        comodel_name="biko.product.prefix",
        domain="[('id', 'in', biko_avail_prefixes)]",
    )

    @api.onchange("biko_product_prefix")
    def _onchange_biko_product_prefix(self):
        if self.biko_product_prefix:
            self.uktzed_id = self.biko_product_prefix.uktzed_id

    @api.model
    def create(self, vals):
        if "categ_id" not in vals and "biko_product_prefix" in vals:
            categories = self.env["product.category"].search(
                [("biko_product_prefix_ids.id", "=", vals["biko_product_prefix"])]
            )
            if categories:
                vals["categ_id"] = categories[0].id

        return super().create(vals)
