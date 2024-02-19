from odoo import fields, models


class ResPartner(models.Model):
    """
    Added dealer code for search when loading
    """

    _inherit = "res.partner"

    dealer_code = fields.Char(
        "Dealer code",
        copy=False,
    )
