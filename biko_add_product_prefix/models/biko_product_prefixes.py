from random import randint

from odoo import fields, models


class BikoProductClass(models.Model):
    _name = "biko.product.prefix"
    _order = "name"

    name = fields.Char(string="Name")
    name_rus = fields.Char(string="Name (RUS)")

    def _get_default_color(self):
        return randint(1, 11)  # nosec

    color = fields.Integer(string="Color Index", default=_get_default_color)
    uktzed_id = fields.Many2one(
        comodel_name="catalog.uktzed",
        string="UKTZED",
        index=True,
        ondelete="set null",
        help="Ukrainian classification of foreign economic activity goods",
    )
