from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from odoo.addons.delivery_novaposhta.models.TTN import date_to_str
from odoo.addons.delivery_novaposhta.models.utils import APIRequest


class NovaPoshtaTTN(models.Model):
    _inherit = "delivery_novaposhta.ttn"

    picking_id = fields.Many2one(comodel_name="stock.picking")
    recipient_id = fields.Many2one(comodel_name="res.partner")
    afterpayment_check = fields.Boolean(string="Afterpayment check", default=False)
    np_length = fields.Integer(
        string="Length (cm)",
        help="The cargo length (cm)",
    )
    np_width = fields.Integer(
        string="Width (cm)",
        help="The cargo width (cm)",
    )
    np_height = fields.Integer(
        string="Height (cm)",
        help="The cargo height (cm)",
    )

    biko_dropshipping = fields.Boolean(string="Dropshipping")

    def _data_from_sale_order(self):
        """Получение данных с заказа продаж, что б ручкамине заполнять"""

        for record in self:
            # product data
            if not self._context.get("autocreate"):
                record.seats_amount = record.order_to_deliver.seats_amount
                address = record.order_to_deliver.partner_shipping_id
                if address:
                    record.recipient_city = address.np_city
                    record.streets = address.np_city
            delivery_np = self.env.ref("novaposhta_data.product_product_delivery_np")
            order_line = record.order_to_deliver.order_line.filtered(
                lambda ol, delivery_np=delivery_np: ol.product_id != delivery_np
            )
            if record.cost == 0:
                cost = sum([ol.price_total for ol in order_line])
                currency_uah = self.env.ref("base.UAH")
                order_currency = record.order_to_deliver.currency_id
                if currency_uah != order_currency:
                    cost = currency_uah.compute(cost, order_currency)
                record.cost = cost

            record.recipient_type = record.order_to_deliver.partner_id.np_type
            if record.order_to_deliver.partner_id.np_type.ref == "Organization":
                record.recipient_name_organization = record.order_to_deliver.partner_id
                # record.recipient_name = record.order_to_deliver.biko_recipient_id
            # else:
            # record.recipient_name = record.order_to_deliver.biko_recipient_id
            record.recipient_name = record.recipient_id
            # salesperson
            record.salesperson = record.order_to_deliver.user_id

    def add_organization(self):
        """То же самое но для организаций.
        Каждая организация это контрагент(не одушный, нпшный)
        и у них должны быть контактные лица. Все, что является
        компанией в оду, должны быть организациями у нп и все сотрудники
        этой компании должны стать ее контактными лицами.
        """

        key = self.get_api_key()

        data = {
            "apiKey": key.key,
            "modelName": "Counterparty",
            "calledMethod": "save",
            "methodProperties": {
                "CityRef": self.recipient_name_organization.np_city.ref,
                "FirstName": self.recipient_name_organization.np_name,
                "MiddleName": "",
                "LastName": "",
                "Phone": "",
                "Email": "",
                "EDRPOU": self.recipient_name_organization.enterprise_code,
                "CounterpartyType": "Organization",
                "CounterpartyProperty": "Recipient",
                "OwnershipForm": self.recipient_name_organization.np_ownership.ref,
            },
        }

        try:
            response = APIRequest.get_data(data)
        except ConnectionError as conn_error:
            raise ValidationError(_("Connection Error")) from conn_error
        if isinstance(response, dict):
            raise ValidationError(
                _("Data was faulty!\nData: {data}\nResponse: {response}").format(
                    data=data, response=response
                )
            )
        self.recipient_name_organization.ref = response[0]["Ref"]

        first_name, last_name, middle_name = self.split_name()

        data = {
            "apiKey": key.key,
            "modelName": "ContactPerson",
            "calledMethod": "save",
            "methodProperties": {
                "CounterpartyRef": self.recipient_name_organization.ref,
                "FirstName": first_name,
                "LastName": last_name,
                "MiddleName": middle_name,
                "Phone": self.recipient_phone,
            },
        }

        try:
            response = APIRequest.get_data(data)
        except ConnectionError as conn_error:
            raise ValidationError(_("Connection Error")) from conn_error
        if isinstance(response, dict):
            raise ValidationError(
                _("Data was faulty:\n {response}").format(response=response)
            )
        self.recipient_name.np_ref = response[0]["Ref"]

        return self.recipient_name_organization.ref, response[0]["Ref"]

    @api.model
    def create(self, vals):
        """Один из самых потных кусков. Тут вся магия(почти)."""

        record = super(NovaPoshtaTTN, self.with_context(create=True)).create(vals)

        if self._context.get("create"):
            return record
        key = self.get_api_key()
        vals["company_id"] = key.company_id.id
        if self._context.get("autocreate"):
            record._data_from_sale_order()
            record._get_phone_from_recipient()
            record._compute_get_rec_type_ref()
            record._cargo_type_change()
        record = record.with_context(no_update_np=True)
        cost = record.cost

        data = {
            "apiKey": key.key,
            "modelName": "InternetDocument",
            "calledMethod": "save",
            "methodProperties": {
                "NewAddress": "0",
                "Description": "Музичні інструменти (музичні товари)",
                "InfoRegClientBarcodes": record.name,
                "PayerType": record.payer_type.ref,
                "PaymentMethod": record.payment_method.ref,
                "CargoType": record.cargo_type.ref,
                "ServiceType": record.service_type.ref,
                "DateTime": date_to_str(record.datetime),
                "Sender": key.senderref,
                "CitySender": record.city_sender.ref,
                "SenderAddress": record.sender_warehouse.ref,
                "ContactSender": record.contact_sender.ref,
                "SendersPhone": record.contact_sender.phones,
                "SeatsAmount": record.seats_amount,
                "Cost": cost,
                "VolumeGeneral": record.general_volume,
                "Weight": record.weight,
            },
        }

        if record.seats_amount > 1:
            optional_seats = []
            for rec in record.picking_id.picking_seats_ids:
                optional_seats.append(
                    {
                        "volumetricVolume": rec.np_shipping_volume,
                        "volumetricWidth": rec.np_width,
                        "volumetricLength": rec.np_length,
                        "volumetricHeight": rec.np_height,
                        "weight": rec.np_shipping_weight,
                    }
                )
            data["methodProperties"].update(
                {
                    "OptionsSeat": optional_seats,
                    "Weight": sum(
                        record.picking_id.picking_seats_ids.mapped("np_shipping_weight")
                    ),
                }
            )

        # Костыль, при безналичном расчете платильщик может быть только отправитель
        # if data['methodProperties']['PayerType'] == 'Recipient':
        #     data['methodProperties']['PaymentMethod'] = 'Cash'

        # backward money
        if record.backward_money:
            data["methodProperties"].update(
                {
                    "BackwardDeliveryData": [
                        {
                            "PayerType": record.bm_payer_type.ref,
                            "CargoType": "Money",
                            "RedeliveryString": record.backward_money_costs,
                        }
                    ],
                }
            )

        if record.afterpayment_check:
            data["methodProperties"].update(
                {
                    "AfterpaymentOnGoodsCost": record.backward_money_costs,
                }
            )

        if record.cargo_type.ref == "TiresWheels":
            # """Колесам нужно отправить доп. параметр с обисанием"""
            data["methodProperties"].update(
                {
                    "CargoDetails": [
                        {
                            "CargoDescription": record.wheels_type.ref,
                            "Amount": record.amount,
                        }
                    ],
                    "SeatsAmount": record.amount,
                }
            )
            record.write(
                {
                    "seats_amount": record.amount,
                }
            )
        elif record.cargo_type.ref == "Pallet":
            raise ValidationError(_("Pallets are bugged and not working"))

        if record.recipient_type.ref == "Organization" and not record.biko_dropshipping:
            # "Отправка организации и ее контакному лицу"

            organization_ref, contact_person_ref = record.add_organization()
            if record.service_type.ref == "WarehouseDoors":
                data["methodProperties"].update(
                    {
                        "NewAddress": "1",
                        "Recipient": organization_ref,
                        "ContactRecipient": contact_person_ref,
                        "CityRecipient": record.recipient_city.ref,
                        "RecipientCityName": record.recipient_city.name,
                        "RecipientHouse": str(record.recipient_house),
                        "RecipientFlat": str(record.recipient_flat),
                        "RecipientsPhone": record.recipient_phone,
                    }
                )
            else:
                data["methodProperties"].update(
                    {
                        "Recipient": organization_ref,
                        "ContactRecipient": contact_person_ref,
                        "RecipientAddress": record.recipient_warehouse.ref,
                        "RecipientsPhone": record.recipient_phone,
                        "CityRecipient": record.recipient_city.ref,
                        "RecipientCityName": record.recipient_city.name,
                    }
                )
        else:
            if record.recipient_phone:
                phone = record.recipient_phone
            else:
                child = record.recipient_name.child_ids
                phones = [c.mobile for c in child if c.mobile]
                if phones:
                    phone = phones[0]
                else:
                    raise ValidationError(_("Field phone is empty"))

            # """ Отправка приватному контактному лицу """

            private_person_ref, contact_person_ref = record.add_privat_person()
            if record.service_type.ref in ["WarehouseDoors", "DoorsDoors"]:
                data["methodProperties"].update(
                    {
                        "NewAddress": "1",
                        "RecipientName": record.recipient_name.name,
                        "RecipientCityName": record.recipient_city.name,
                        "RecipientAddressName": record.streets.name,
                        "RecipientHouse": str(record.recipient_house),
                        "RecipientFlat": str(record.recipient_flat),
                        "RecipientsPhone": phone,
                    }
                )
            else:
                data["methodProperties"].update(
                    {
                        "Recipient": private_person_ref,
                        "ContactRecipient": contact_person_ref,
                        "RecipientAddress": record.recipient_warehouse.ref,
                        "RecipientAddressName": record.recipient_warehouse.name,
                        "RecipientsPhone": phone,
                        "CityRecipient": record.recipient_city.ref,
                        "RecipientCityName": record.recipient_city.name,
                    }
                )

        if record.service_type.ref == "WarehousePostomat":
            data["methodProperties"].update(
                {
                    "NewAddress": "0",
                    "OptionsSeat": [
                        {
                            "volumetricVolume": record.general_volume,
                            "volumetricWidth": record.np_width,
                            "volumetricLength": record.np_length,
                            "volumetricHeight": record.np_height,
                            "weight": record.weight,
                        }
                    ],
                }
            )

        return record.send_ttn(data)
