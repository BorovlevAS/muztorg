from odoo import _, fields, models


class ProductPackaging(models.Model):
    _inherit = "product.packaging"

    package_carrier_type = fields.Selection(selection_add=[("np", _("Nova poshta"))])
