from odoo import models


class ResPartner(models.Model):
    _inherit = "res.partner"

    def write(self, vals):
        vals_partner = {}
        res = super().write(vals)
        for rec in self:
            if not rec.parent_id and vals.get("property_product_pricelist"):
                partner_contacts = self.env["res.partner"].search(
                    [
                        ("parent_id", "=", rec.id),
                        ("type", "=", "contact"),
                    ]
                )
                for partner in partner_contacts:
                    vals_partner[
                        "property_product_pricelist"
                    ] = rec.property_product_pricelist.id
                    partner.write(vals_partner)
        return res
