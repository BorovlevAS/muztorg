from odoo import fields, models


class BikoProductClass(models.Model):
    _name = "biko.product.class"
    _order = "name"

    name = fields.Char(string="Name")
