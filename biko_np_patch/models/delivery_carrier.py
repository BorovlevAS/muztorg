from odoo import _, models
from odoo.exceptions import UserError


class ProviderNP(models.Model):
    _inherit = "delivery.carrier"

    def np_send_shipping(self, pickings):
        for picking in pickings:
            error_messages = []
            error = False

            if picking.cost == 0:
                error_messages.append(_("Cost not specified"))
                error = True

            if picking.seats_amount == 0:
                error_messages.append(_("Seats amount doesn't specified"))
                error = True
            elif picking.seats_amount == 1:
                if picking.np_shipping_weight == 0:
                    error_messages.append(_("Shipping weight not specified"))
                    error = True

                if picking.np_shipping_volume == 0:
                    error_messages.append(_("Shipping volume not specified"))
                    error = True
            else:
                for rec in picking.picking_seats_ids:
                    if rec.np_shipping_weight == 0 or rec.np_shipping_volume == 0:
                        error_messages.append(_("Seats data is not specified"))
                        error = True
                        break

            if not picking.biko_recipient_id:
                error_messages.append(_("Recipient person not specified"))
                error = True
            elif not picking.biko_recipient_id.mobile:
                error_messages.append(_("Recipient person mobile not specified"))
                error = True

            if not picking.recipient_city:
                error_messages.append(_("Recipient city is not specified"))
                error = True

            if (
                picking.service_type.ref
                in [
                    "DoorsWarehouse",
                    "WarehouseWarehouse",
                ]
            ) and (not picking.recipient_warehouse):
                error_messages.append(_("Warehouse is not specified"))
                error = True

            if error:
                raise UserError("\n".join(error_messages))

            data = {
                "name": picking.sale_id.name,
                "order_to_deliver": picking.sale_id.id,
                "salesperson": picking.sale_id.user_id.id,
                "payer_type": picking.payer_type.id or self.np_payer_type.id,
                "payment_method": picking.payment_method.id
                or self.np_payment_method.id,
                "cargo_type": picking.cargo_type.id or self.np_cargo_type.id,
                "city_sender": picking.sender_city.id or self.np_city_sender.id,
                "sender_warehouse": picking.sender_warehouse.id
                or self.np_sender_warehouse.id,
                "contact_sender": self.np_contact_sender.id,
                "service_type": picking.service_type.id or self.np_service_type.id,
                "datetime": picking.scheduled_date,
                "seats_amount": picking.seats_amount,
                "recipient_city": picking.recipient_city.id
                or picking.sale_id.partner_shipping_id.np_city.id,
                "cost": picking.cost,
                "weight": picking.np_shipping_weight,
                "np_length": picking.np_length,
                "np_width": picking.np_width,
                "np_height": picking.np_height,
                "general_volume": picking.np_shipping_volume,
                "recipient_id": picking.biko_recipient_id.id,
                "biko_dropshipping": picking.biko_dropshipping,
                "picking_id": picking.id,
            }
            if picking.backward_money:
                data.update(
                    {
                        "backward_money": picking.backward_money,
                        "bm_payer_type": picking.bm_payer_type.id,
                        "backward_money_costs": picking.backward_money_costs,
                    }
                )
            if picking.afterpayment_check:
                data.update(
                    {
                        "afterpayment_check": picking.afterpayment_check,
                        "backward_money_costs": picking.backward_money_costs,
                    }
                )

            service_type = (
                self.env["delivery_novaposhta.service_types"]
                .browse(data["service_type"])
                .ref
            )
            if service_type in [
                "DoorsDoors",
                "WarehouseDoors",
            ]:
                data.update(
                    {
                        "recipient_house": picking.recipient_house
                        or picking.sale_id.partner_shipping_id.house,
                        "recipient_flat": picking.recipient_flat
                        or picking.sale_id.partner_shipping_id.flat,
                        "streets": picking.streets.id
                        or picking.sale_id.partner_shipping_id.np_street.id,
                    }
                )
            else:
                data.update(
                    {
                        "recipient_warehouse": picking.recipient_warehouse.id
                        or picking.sale_id.partner_shipping_id.np_warehouse.id,
                    }
                )
            if self.notification:
                ttn = (
                    self.env["delivery_novaposhta.ttn"]
                    .with_context(autocreate=True)
                    .create(data)
                )

            else:
                ttn = (
                    self.env["delivery_novaposhta.ttn"]
                    .with_context(autocreate=True, notif=True)
                    .create(data)
                )
            if ttn:
                picking.ttn = ttn
                res = []
                cost = ttn.estimated_costs
                shipping_data = {"exact_price": cost, "tracking_number": ttn.doc_number}
                res += [shipping_data]
            else:
                shipping_data = {
                    "exact_price": 101.0,
                    "tracking_number": 20450090830943,
                }
                res += [shipping_data]
        return res
