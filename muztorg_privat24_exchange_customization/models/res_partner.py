from odoo import api, fields, models


class Partner(models.Model):
    _inherit = "res.partner"
    company_registry = fields.Char(
        compute="_compute_company_registry",
        store=True,
    )

    @api.depends("enterprise_code")
    def _compute_company_registry(self):
        for partner in self:
            partner.company_registry = partner.enterprise_code
