from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class NumberDaysReservation(models.Model):
    _name = "number.days.reservation"

    name = fields.Char("Name", required=True, default="Number Of Days", readonly=True)
    nb_days = fields.Float(string="Days", required=True, default=0)

    @api.constrains("name")
    def _check_nb_days(self):
        if self.search_count([]) > 1:
            raise ValidationError(_("You can not create more than one Global Margin"))
