from odoo import _, api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.model
    def _get_states_sale_order(self):
        return [
            ("draft", _("On approval")),
            ("reserve", _("In reserve")),
            ("waiting", _("Waiting for payment")),
            ("sent", _("Quotation Sent")),
            ("sale", _("Before shipping")),
            ("done", _("Locked")),
            ("cancel", _("Closed")),
        ]

    state = fields.Selection(selection=_get_states_sale_order)
