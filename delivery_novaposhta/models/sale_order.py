from odoo import api, fields, models


class SaleOrder(models.Model):
    # pylint: disable=method-compute
    _inherit = "sale.order"

    delivery_type = fields.Char(compute="_get_delivery_type")
    backward_money = fields.Boolean("C.O.D")
    bm_payer_type = fields.Many2one(
        "delivery_novaposhta.types_of_payers_for_redelivery",
        string="Payer Type",
    )
    seats_amount = fields.Integer("Seats Amount", default=1)

    @api.depends("carrier_id")
    def _get_delivery_type(self):
        for record in self:
            record.delivery_type = record.carrier_id.delivery_type
