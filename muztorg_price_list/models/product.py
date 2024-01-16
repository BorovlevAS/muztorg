from odoo import fields, models


class Product(models.Model):
    _inherit = "product.template"

    biko_mg_id = fields.Many2one(
        string="Product marketing group",
        comodel_name="biko.marketing.group",
    )
