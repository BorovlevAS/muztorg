from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


# class ResConfig(models.TransientModel):
#     _inherit = 'res.config.settings'

class NumberDaysReservation(models.Model):
    _name = 'number.days.reservation'

    name = fields.Char('Name', required=True, default='Number Of Days', readonly=True)
    nb_days = fields.Float(string='Days', required=True, default=0)

    @api.constrains('name')
    def _check_nb_days(self):
        if self.search_count([]) > 1:
            raise ValidationError(_("You can not create more than one Global Margin"))

    # @api.model
    # def get_values(self):
    #     res = super(ResConfig, self).get_values()
    #
    #     ICPSudo = self.env['ir.config_parameter'].sudo()
    #
    #     nb_days = literal_eval(ICPSudo.get_param('odoo_stock_reservation.nb_days', default='1'))
    #
    #     res.update(nb_days=nb_days)
    #     return res
    #
    # def set_values(self):
    #     super(ResConfig, self).set_values()
    #     ICPSudo = self.env['ir.config_parameter'].sudo()
    #     ICPSudo.set_param("odoo_stock_reservation.nb_days", self.nb_days)
