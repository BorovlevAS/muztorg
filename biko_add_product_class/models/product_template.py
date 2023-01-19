# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = "product.template"

    biko_product_class = fields.Many2one(
        string="Product class", comodel_name="biko.product.class"
    )

    biko_product_model = fields.Many2one(
        string="Product model", comodel_name="biko.product.model"
    )

    biko_country = fields.Many2one(
        string="Country", comodel_name="res.country"
    )

    biko_country_customs = fields.Many2one(
        string="Country for custom", comodel_name="res.country"
    )

    biko_character_ukr = fields.Text(
        string='Characteristics (ukr)',
    )
    