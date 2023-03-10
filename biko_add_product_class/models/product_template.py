# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo import _


class ProductTemplate(models.Model):
    _inherit = "product.template"

    biko_product_class = fields.Many2one(
        string="Product class", comodel_name="biko.product.class"
    )

    biko_product_model = fields.Char(
        string="Product model", comodel_name="biko.product.model"
    )

    biko_country = fields.Many2one(string="Country", comodel_name="res.country")

    biko_country_customs = fields.Many2one(
        string="Country for custom", comodel_name="res.country"
    )

    biko_character_ukr = fields.Text(
        string="Characteristics (ukr)",
    )

    biko_vendor_code = fields.Char(string="Vendor Code")

    _sql_constraints = [
        (
            "vendor_code_unique",
            "unique(biko_vendor_code)",
            _("Vendor code must be unique"),
        )
    ]

    biko_control_code = fields.Char(string="Control code")

    @api.model
    def create(self, vals):

        if not vals.get("biko_control_code", False):
            vals["biko_control_code"] = self.env["ir.sequence"].next_by_code(
                "biko.product.control.code"
            )

        return super().create(vals)

    def write(self, vals):
        for rec in self:
            if (not "biko_control_code" in vals) and (not rec.biko_control_code):
                vals["biko_control_code"] = self.env["ir.sequence"].next_by_code(
                    "biko.product.control.code"
                )

        return super().write(vals)

    @api.model
    def _name_search(
        self, name, args=None, operator="ilike", limit=100, name_get_uid=None
    ):
        if not args:
            args = []
        if name:
            product_ids = list(
                self._search(
                    [("biko_control_code", "=", name)] + args,
                    limit=limit,
                    access_rights_uid=name_get_uid,
                )
            )

            if not product_ids:
                return super(ProductTemplate, self)._name_search(
                    name,
                    args,
                    operator=operator,
                    limit=limit,
                    name_get_uid=name_get_uid,
                )

        else:

            return super(ProductTemplate, self)._name_search(
                name, args, operator=operator, limit=limit, name_get_uid=name_get_uid
            )

        return product_ids
