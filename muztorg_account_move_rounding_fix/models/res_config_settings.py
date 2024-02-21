from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    max_avail_diff = fields.Float(string="Max Available Difference")


class Settings(models.TransientModel):
    _inherit = "res.config.settings"
    max_avail_diff = fields.Float(
        related="company_id.max_avail_diff",
        string="Max Available Difference",
        readonly=False,
    )
