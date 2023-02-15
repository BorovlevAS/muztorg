from odoo import api, models, _
from odoo.exceptions import ValidationError, UserError

import logging

_logger = logging.getLogger(__name__)

try:
    import phonenumbers

    def check_phone_mobile(number, country_code):
        try:
            phone_nbr = phonenumbers.parse(
                number, region=country_code, keep_raw_input=True
            )

            op_code = "0" + str(phone_nbr.national_number)[0:2]

            return (
                op_code
                in [
                    "039",
                    "050",
                    "063",
                    "066",
                    "067",
                    "068",
                    "073",
                    "091",
                    "092",
                    "093",
                    "094",
                    "095",
                    "096",
                    "097",
                    "098",
                    "099",
                ]
            ), op_code

        except phonenumbers.phonenumberutil.NumberParseException as e:
            raise UserError(
                _("Unable to parse %(phone)s: %(error)s", phone=number, error=str(e))
            )

except ImportError:
    _logger.error("Error importing module phonenumbers")

    def check_phone_mobile(nomber, country_code):
        return True


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.constrains("mobile")
    def _check_mobile(self):

        for rec in self:
            if rec.mobile and rec.company_type == "person":
                result, op_code = check_phone_mobile(
                    rec.mobile, rec.country_id.code if rec.country_id else "UA"
                )

                if not result:
                    raise ValidationError(
                        _("{} is not a mobile operator code").format(op_code)
                    )

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
