from odoo import _, api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    service_type = fields.Many2one(
        "delivery_novaposhta.service_types", string="Service Types"
    )
    service_type_ref = fields.Char(related="service_type.ref", help="Technical field")
    recipient_house = fields.Char(string="Recipient House")
    recipient_flat = fields.Integer(string="Recipient Flat")
    streets = fields.Many2one("delivery_novaposhta.streets_list", string="Street")
    description_street = fields.Char(string="Full address")
    ttn = fields.Many2one("delivery_novaposhta.ttn")
    seats_amount = fields.Integer("Seats Amount")
    backward_money = fields.Boolean("C.O.D")
    bm_payer_type = fields.Many2one(
        "delivery_novaposhta.types_of_payers_for_redelivery", string="Payer Type"
    )
    payer_type = fields.Many2one(
        "delivery_novaposhta.types_of_payers", string="Payer Type"
    )
    backward_money_costs = fields.Float("Costs")
    invoice_id = fields.Many2one("account.move", string="Invoice")
    recipient_city = fields.Many2one(
        "delivery_novaposhta.cities_list", string="Recipient City"
    )
    cargo_type = fields.Many2one("delivery_novaposhta.cargo_types", string="Cargo Type")
    payment_method = fields.Many2one(
        "delivery_novaposhta.payments_forms", string="Payment Method"
    )
    recipient_warehouse = fields.Many2one(
        "delivery_novaposhta.warehouse",
        domain="[('cityref', '=', rec_city_ref)]",
        string="Recipient Warehouse",
    )
    sender_city = fields.Many2one(
        "delivery_novaposhta.cities_list",
        string="Sender City",
    )
    sender_warehouse = fields.Many2one(
        "delivery_novaposhta.warehouse",
        domain="[('cityref', '=', send_city_ref)]",
        string="Sender Warehouse",
    )
    rec_city_ref = fields.Char(related="recipient_city.ref", help="Technical field")
    send_city_ref = fields.Char(related="sender_city.ref", help="Technical field")

    @api.model
    def create(self, vals):
        if vals.get("carrier_id"):
            carrier_id = self.env["delivery.carrier"].browse(vals["carrier_id"])
            order = self.env["sale.order"].search([("name", "=", vals.get("origin"))])
            if carrier_id.delivery_type == "np":
                vals["service_type"] = carrier_id.np_service_type.id
                vals["payer_type"] = carrier_id.np_payer_type.id
                vals["sender_warehouse"] = carrier_id.np_sender_warehouse.id
                vals["sender_city"] = carrier_id.np_city_sender.id
                vals["cargo_type"] = carrier_id.np_cargo_type.id
                vals["payment_method"] = carrier_id.np_payment_method.id
                if order:
                    vals["seats_amount"] = order.seats_amount
                    vals["backward_money"] = (
                        vals.get("backward_money") or order.backward_money
                    )
                    vals["bm_payer_type"] = (
                        vals.get("bm_payer_type") or order.bm_payer_type.id
                    )
                    vals["backward_money_costs"] = (
                        vals.get("backward_money_costs") or order.amount_total
                    )
                    vals["recipient_city"] = (
                        order.partner_shipping_id.np_city.id or False
                    )
                    vals["recipient_warehouse"] = (
                        order.partner_shipping_id.np_warehouse.id or False
                    )
                    vals["streets"] = order.partner_shipping_id.np_street.id or False
                    vals["recipient_house"] = order.partner_shipping_id.house or False
                    vals["recipient_flat"] = order.partner_shipping_id.flat or False
        res = super().create(vals)
        return res

    def open_ttn(self):
        return {
            "type": "ir.actions.act_window",
            "name": "TTN",
            # 'view_type': 'form',
            "view_mode": "form",
            "res_model": "delivery_novaposhta.ttn",
            "res_id": self.ttn.id,
            "target": "current",
        }

    def open_invoice(self):
        return {
            "type": "ir.actions.act_window",
            "name": "TTN",
            # 'view_type': 'form',
            "view_mode": "form",
            "res_model": "account.move",
            "res_id": self.invoice_id.id,
            "target": "current",
        }

    def print_document_pdf(self):
        key = self.ttn.get_api_key()
        url = (
            "https://my.novaposhta.ua/orders/printDocument/orders[]/"
            + self.ttn.ref
            + "/type/pdf/apiKey/"
            + key.key
        )
        return {
            "name": _("TTN"),
            "type": "ir.actions.act_url",
            "url": url,
            "target": "new",
        }

    def print_barcode_pdf(self):
        key = self.ttn.get_api_key()
        url = (
            "https://my.novaposhta.ua/orders/printMarkings/orders[]/"
            + self.ttn.ref
            + "/type/pdf/apiKey/"
            + key.key
        )
        return {
            "name": _("TTN"),
            "type": "ir.actions.act_url",
            "url": url,
            "target": "new",
        }
