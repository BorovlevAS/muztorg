from odoo import fields, models


class ReturnPicking(models.TransientModel):
    _inherit = "stock.return.picking"

    biko_reason_return = fields.Char(
        "Reason for return",
        required=True,
    )

    def _create_returns(self):
        """in this function the picking is marked as return"""
        new_picking, pick_type_id = super()._create_returns()
        picking = self.env["stock.picking"].browse(new_picking)
        picking.write({"biko_reason_return": self.biko_reason_return})

        picking.write({"service_type": False})
        picking.write({"service_type_ref": False})
        picking.write({"recipient_house": False})
        picking.write({"recipient_flat": False})
        picking.write({"streets": False})
        picking.write({"description_street": False})
        picking.write({"ttn": False})
        picking.write({"seats_amount": False})
        picking.write({"backward_money": False})
        picking.write({"bm_payer_type": False})
        picking.write({"payer_type": False})
        picking.write({"backward_money_costs": False})
        picking.write({"invoice_id": False})
        picking.write({"recipient_city": False})
        picking.write({"cargo_type": False})
        picking.write({"payment_method": False})
        picking.write({"recipient_warehouse": False})
        picking.write({"sender_city": False})
        picking.write({"sender_warehouse": False})
        picking.write({"rec_city_ref": False})
        picking.write({"send_city_ref": False})

        picking.write({"cost": False})
        picking.write({"np_shipping_weight": False})
        picking.write({"np_shipping_volume": False})
        picking.write({"np_length": False})
        picking.write({"np_width": False})
        picking.write({"np_height": False})
        picking.write({"biko_volume_weight": False})
        picking.write({"comment": False})
        picking.write({"biko_recipient_mobile": False})
        picking.write({"biko_1c_phone": False})
        picking.write({"biko_dropshipping": False})
        picking.write({"biko_carrier_id": False})
        picking.write({"picking_seats_ids": False})

        picking.write({"carrier_id": False})

        return new_picking, pick_type_id
