from odoo import api, models, _
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.constrains("mobile")
    def _check_mobile(self):

        for rec in self:
            if rec.mobile and rec.company_type == "person":
                client_names = (
                    self.env["res.partner"]
                    .search([("mobile", "=", rec.mobile), ("id", "!=", rec.id)])
                    .mapped("name")
                )
                if client_names:

                    message = _(
                        "Client{} with mobile number {} is already exists\n"
                    ).format("s" if len(client_names) > 1 else "", rec.mobile)
                    for name in client_names:
                        message += name + "\n"

                    raise ValidationError(message)
