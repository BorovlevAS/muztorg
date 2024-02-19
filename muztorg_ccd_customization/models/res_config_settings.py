from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    ccd_journal_id = fields.Many2one(comodel_name="account.journal")
    ccd_vat_product_id = fields.Many2one(
        comodel_name="product.product",
        string="Product for customs broker",
    )
    ccd_vat_tax_id = fields.Many2one(
        comodel_name="account.tax",
        string="Default VAT Tax",
    )


class Settings(models.TransientModel):
    _inherit = "res.config.settings"
    ccd_vat_product_id = fields.Many2one(
        comodel_name="product.product",
        related="company_id.ccd_vat_product_id",
        string="Product for customs broker",
        readonly=False,
    )
    ccd_vat_tax_id = fields.Many2one(
        comodel_name="account.tax",
        related="company_id.ccd_vat_tax_id",
        string="Default VAT Tax",
        readonly=False,
    )
