from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    biko_uah_pricelist_id = fields.Many2one(
        comodel_name="product.pricelist",
        string="Default UAH pricelist",
    )


class Settings(models.TransientModel):
    _inherit = "res.config.settings"
    biko_uah_pricelist_id = fields.Many2one(
        comodel_name="product.pricelist",
        related="company_id.biko_uah_pricelist_id",
        string="Default UAH pricelist",
        readonly=False,
    )
