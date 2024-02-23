from odoo import fields, models


class ResCompany(models.Model):
    """Add price list parameters"""

    _inherit = "res.company"

    biko_price_dealer = fields.Many2one(
        comodel_name="product.pricelist",
        string="Dealer price",
    )

    biko_price_retail = fields.Many2one(
        comodel_name="product.pricelist",
        string="Retail price",
    )

    biko_price_USD_ids = fields.Many2many(
        comodel_name="product.pricelist",
        string="USD prices",
    )

    # credit_policy_id = fields.Many2one(
    #     comodel_name="credit.control.policy",
    #     string="Credit Control Policy",
    #     readonly=False,
    #     help="The Credit Control Policy used "
    #     "on partners by default. "
    #     "This setting can be overridden"
    #     " on partners or invoices.",
    # )
