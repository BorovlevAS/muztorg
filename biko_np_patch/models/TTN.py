from odoo import _, fields, models
from odoo.addons.delivery_novaposhta.models.utils import APIRequest
from odoo.exceptions import ValidationError


class NovaPoshtaTTN(models.Model):
    _inherit = "delivery_novaposhta.ttn"

    recipient_id = fields.Many2one(comodel_name="res.partner")

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
            # removing caluculdating
            # all fields we will fill from picking
            # if record.seats_amount > 0:
            #     if record.weight == 0:
            #         record.weight = (
            #             sum(
            #                 [
            #                     (line.product_id.weight * line.product_uom_qty)
            #                     for line in order_line
            #                 ]
            #             )
            #             or 0.0
            #         )
            #     if record.general_volume == 0:
            #         record.general_volume = (
            #             sum(
            #                 [
            #                     (line.product_id.volume * line.product_uom_qty)
            #                     for line in order_line
            #                 ]
            #             )
            #             or 0.0
            #         )
            # recipient data
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
