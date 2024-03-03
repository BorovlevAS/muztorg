# Copyright 2023 Domatix - Carlos Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    uktzed_id = fields.Many2one(
        comodel_name="catalog.uktzed", string="UKTZED", related="product_id.uktzed_id"
    )
    biko_country_name = fields.Many2one(
        string="Country of manufacture",
        related="product_id.product_tmpl_id.biko_country",
        comodel_name="res.country",
    )
