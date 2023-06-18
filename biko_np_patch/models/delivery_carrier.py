from odoo import fields, models


class ProviderNP(models.Model):
    _inherit = "delivery.carrier"

    def np_send_shipping(self, pickings):
        for picking in pickings:
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
            }
            if picking.backward_money:
                data.update(
                    {
                        "backward_money": picking.backward_money,
                        "bm_payer_type": picking.bm_payer_type.id,
                        "backward_money_costs": picking.backward_money_costs,
                    }
                )
            if self.env["delivery_novaposhta.service_types"].browse(
                data["service_type"]
            ).ref in [
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
                if "" in self.np_payer_type.ref == "Sender":
                    np_partner = self.env.ref("novaposhta_data.np_partner")
                    np_product = self.env.ref(
                        "novaposhta_data.product_product_delivery_np"
                    )
                    if np_partner and np_product:
                        invoice_data = {
                            "name": "",
                            "move_type": "in_invoice",
                            "partner_id": np_partner.id,
                            "invoice_date": fields.Datetime.now(),
                            "invoice_line_ids": [
                                (
                                    0,
                                    0,
                                    {
                                        "name": np_product.name,
                                        "product_id": np_product.id,
                                        "quantity": 1,
                                        "product_uom_id": np_product.uom_id.id,
                                        "price_unit": ttn.estimated_costs,
                                        "analytic_account_id": picking.sale_id.analytic_account_id.id,
                                        "account_id": np_partner.property_account_receivable_id.id,
                                    },
                                )
                            ],
                            "currency_id": self.env.ref("base.UAH").id,
                        }
                        picking.invoice_id = self.env["account.move"].create(
                            invoice_data
                        )
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
