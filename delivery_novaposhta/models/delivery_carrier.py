import logging
import threading

from odoo import _, api, fields, models
from requests import ConnectionError

from .utils import APIRequest

_logger = logging.getLogger(__name__)


class ProviderNP(models.Model):
    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(
        selection_add=[("np", _("Nova poshta"))], ondelete={"np": "cascade"}
    )

    np_key = fields.Many2one("delivery_novaposhta.api_key", string="Key")
    np_service_type = fields.Many2one(
        "delivery_novaposhta.service_types", string="Service Type"
    )
    np_cargo_type = fields.Many2one(
        "delivery_novaposhta.cargo_types", string="Cargo Type"
    )
    np_contact_sender = fields.Many2one(
        "delivery_novaposhta.sender_contact", string="Sender Contact"
    )
    np_sender_warehouse = fields.Many2one(
        "delivery_novaposhta.warehouse",
        domain="[('cityref', '=', np_city_ref)]",
        string="Sender Warehouse",
    )
    np_city_sender = fields.Many2one(
        "delivery_novaposhta.cities_list", string="Sender City"
    )
    np_payer_type = fields.Many2one(
        "delivery_novaposhta.types_of_payers", string="Payer Type"
    )
    np_payment_method = fields.Many2one(
        "delivery_novaposhta.payments_forms", string="Payment Method"
    )
    np_city_ref = fields.Char(related="np_city_sender.ref", help="Technical field")
    np_default_packaging_id = fields.Many2one(
        "product.packaging", string="Default Package Type"
    )
    notification = fields.Boolean("notification", default=True)
    np_default_vendor_delivery = fields.Many2one(
        "res.partner",
        "Vendor delivery",
        # domain="[('supplier','=',True)]",
        default=lambda self: self.env.ref("novaposhta_data.np_partner").id,
    )

    def np_send_shipping(self, pickings):
        for picking in pickings:
            data = {
                "name": picking.sale_id.name,
                "order_to_deliver": picking.sale_id.id,
                "salesperson": picking.sale_id.user_id.id,
                "payer_type": self.np_payer_type.id,
                "payment_method": picking.payment_method.id
                or self.np_payment_method.id,
                "cargo_type": picking.cargo_type.id or self.np_cargo_type.id,
                "city_sender": picking.sender_city.id or self.np_city_sender.id,
                "sender_warehouse": self.np_sender_warehouse.id
                or picking.sender_warehouse.id,
                "contact_sender": self.np_contact_sender.id,
                "service_type": picking.service_type.id or self.np_service_type.id,
                "datetime": picking.scheduled_date,
                "seats_amount": picking.seats_amount,
                "recipient_city": picking.recipient_city.id
                or picking.sale_id.partner_shipping_id.np_city.id,
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
            ).ref in ["DoorsDoors", "WarehouseDoors"]:
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

    @api.model
    def np_rate_shipment(self, order):
        """{
           "modelName": "InternetDocument",
           "calledMethod": "getDocumentPrice",
           "methodProperties": {
              "CitySender": "8d5a980d-391c-11dd-90d9-001a92567626",
              "CityRecipient": "db5c88e0-391c-11dd-90d9-001a92567626",
              "Weight": "10",
              "ServiceType": "DoorsDoors",
              "Cost": "100",
              "CargoType": "Cargo",
              "SeatsAmount": "10",
                "PackCalculate": {
                    "PackCount": "1",
                    "PackRef": "1499fa4a-d26e-11e1-95e4-0026b97ed48a"
                },
              "RedeliveryCalculate": {
                 "CargoType": "Money",
                 "Amount": "100"
              }
           },
           "apiKey": "[ВАШ КЛЮЧ]"
        }"""

        try:
            key = (
                self.env["delivery_novaposhta.api_key"]
                .search([("active", "=", True)])[0]
                .key
            )
        except IndexError:
            return {
                "success": False,
                "price": 0.0,
                "error_message": "There is no active API key!",
            }

        currency_uah = self.env.ref("base.UAH")
        order_currency = order.currency_id
        cost = order_currency.compute(order.amount_total, currency_uah)

        # Estimate weight of the sale order; will be definitely recomputed on the picking field "weight"
        weight = (
            sum(
                [
                    line.product_id.weight * line.product_uom_qty
                    for line in order.order_line
                ]
            )
            or 0.0
        )
        volume = (
            sum(
                [
                    line.product_id.volume * line.product_uom_qty
                    for line in order.order_line
                ]
            )
            or 0.0
        )
        address = order.partner_shipping_id
        city_recipient = address.np_city.ref if address else False
        data = {
            "modelName": "InternetDocument",
            "calledMethod": "getDocumentPrice",
            "methodProperties": {
                "CitySender": self.np_city_sender.ref,
                "CityRecipient": city_recipient,
                "Weight": weight,
                "ServiceType": self.np_service_type.ref,
                "Cost": cost,
                "CargoType": self.np_cargo_type.ref,
                "VolumeGeneral": volume,
                "SeatsAmount": order.seats_amount,
                # "PackCalculate": {
                #     "PackCount": "1",
                #     "PackRef": "1499fa4a-d26e-11e1-95e4-0026b97ed48a"
                # },
                # "RedeliveryCalculate": {
                #    "CargoType": "Money",
                #    "Amount": "100"
                # }
            },
            "apiKey": key,
        }
        try:
            response = APIRequest.get_data(data)
        except ConnectionError:
            return {"success": False, "price": 0.0, "error_message": "Connection Error"}

        if "errors" not in response:
            price = response[0]["Cost"]
            if currency_uah != order_currency:
                price = order_currency.compute(price, currency_uah)
            res = {"success": True, "price": float(price), "warning_message": "Done!"}
            if "TZoneInfo" in response[0]:
                res["warning_message"] = response[0]["TZoneInfo"]["TzoneName"]
        else:
            res = {"success": False, "price": 0.0}
            res["error_message"] = ""
            for error in response["errors"]:
                res["error_message"] += error + "\n"

        return res

    def np_get_tracking_link(self, picking):
        return (
            "https://novaposhta.ua/tracking/?cargo_number=%s"
            % picking.carrier_tracking_ref
        )

    def np_cancel_shipment(self, picking):
        self.env["delivery_novaposhta.ttn"].delete_one()

    def _convert_weight(weight, unit="KG"):
        """Convert picking weight (always expressed in KG) into the specified unit"""
        if unit == "KG":
            return weight
        elif unit == "LB":
            return weight / 0.45359237
        else:
            raise ValueError

    def synchronize(self):
        self.env["delivery_novaposhta.synchronize"].update_values()

    def ttn_synchronize(self):
        self.env["delivery_novaposhta.sync_ttn"].synchronize()


class SynchronizeDict(models.TransientModel):
    _name = "delivery_novaposhta.synchronize"

    def synchronize_thread(self):
        envs = [
            "delivery_novaposhta.cargo_types",
            "delivery_novaposhta.backward_delivery_cargo_type",
            "delivery_novaposhta.pallets_list",
            "delivery_novaposhta.types_of_payers",
            "delivery_novaposhta.types_of_payers_for_redelivery",
            "delivery_novaposhta.pack_list",
            "delivery_novaposhta.tires_wheels_list",
            "delivery_novaposhta.cargo_descritpion_list",
            "delivery_novaposhta.service_types",
            "delivery_novaposhta.types_of_counterparties",
            "delivery_novaposhta.payments_forms",
            "delivery_novaposhta.ownership_forms_list",
            "delivery_novaposhta.cities_list",
            "delivery_novaposhta.warehouse",
            "delivery_novaposhta.areas_list",
            "delivery_novaposhta.streets_list",
        ]
        with api.Environment.manage():
            for env in envs:
                # Create a new environment with new cursor database
                new_cr = self.pool.cursor()
                self = self.with_env(self.env(cr=new_cr))
                self.env[env].update_values()
                new_cr.commit()
                new_cr.close()

    def update_values(self):
        threaded_synchronize = threading.Thread(target=self.synchronize_thread)
        threaded_synchronize.start()
