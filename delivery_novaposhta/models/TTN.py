import logging
from datetime import datetime

from requests import ConnectionError

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from .utils import APIRequest

_logger = logging.getLogger(__name__)

TTN_IGNORE_STATUS = [2, 9, 10, 11, 102, 103, 108, 105, 106]
TTN_NOTIFY_STATUS = [9, 11, 102, 103, 108, 105, 106, 107]


def date_to_str(date):
    return fields.Date.from_string(date).strftime("%d.%m.%Y") if date else False


ttn_fields = {
    "Ref": ["ref"],
    "Description": ["name"],
    "PayerType": ["payer_type", "ref"],
    "PaymentMethod": ["payment_method", "ref"],
    "CargoType": ["cargo_type", "ref"],
    "ServiceType": ["service_type", "ref"],
    "DateTime": ["datetime"],
    "CitySender": ["city_sender", "ref"],
    "SenderAddress": ["sender_warehouse", "ref"],
    # "ContactSender": ['contact_sender', 'ref'],
    # "SendersPhone": ['contact_sender', 'phones'],
    "CityRecipient": ["recipient_city", "ref"],
    "RecipientAddress": ["recipient_warehouse", "ref"],
    "RecipientsPhone": ["recipient_phone"],
    "Weight": ["weight"],
    "SeatsAmount": ["seats_amount"],
    "Cost": ["cost"],
    "VolumeGeneral": ["general_volume"],
    # "Sender": ['contact_sender', 'ref'],
    "CostOnSite": ["estimated_costs"],
    "EstimatedDeliveryDate": ["estimated_delivery_date"],
    "RecipientCounterpartyType": ["recipient_type", "ref"],
    "IntDocNumber": ["doc_number"],
    "StateName": ["status"],
    "StateId": ["status_code"],
    "company_id": ["company_id"],
}
backward_field = {
    "PayerType": ["bm_payer_type", "ref"],
    "RedeliveryString": ["backward_money_costs"],
}


class NovaPoshtaTTN(models.Model):
    _name = "delivery_novaposhta.ttn"

    # NP TTN info
    doc_number = fields.Char(string="Document Number", readonly=True)
    ref = fields.Char(string="Ref", readonly=True)
    estimated_costs = fields.Float(string="Estimated Costs", readonly=True)
    estimated_delivery_date = fields.Date(
        string="Estimated delivery date", readonly=True
    )
    status = fields.Char(string="Status", readonly=True)
    status_code = fields.Integer(
        string="Status code", readonly=True, help="Technical field"
    )
    key = fields.Many2one("delivery_novaposhta.api_key")

    # Sale order
    order_to_deliver = fields.Many2one("sale.order", string="Order to deliver")
    salesperson = fields.Many2one("res.users", string="Salesperson")

    # General info
    name = fields.Char(string="Description")
    payer_type = fields.Many2one(
        "delivery_novaposhta.types_of_payers", string="Payer Type"
    )
    payment_method = fields.Many2one(
        "delivery_novaposhta.payments_forms", string="Payment Method"
    )
    cargo_type = fields.Many2one(
        "delivery_novaposhta.cargo_types", string="Cargo Types"
    )
    cargo_type_ref = fields.Char(
        compute="_compute_get_cargo_type_ref", help="Technical Field"
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        readonly=True,
        default=lambda self: self.env.user.company_id,
    )

    # Files
    waybill = fields.Binary()
    barcode = fields.Binary()

    # Backward Money
    backward_money = fields.Boolean("C.O.D")
    bm_payer_type = fields.Many2one(
        "delivery_novaposhta.types_of_payers_for_redelivery",
        string="Payer Type",
    )
    backward_money_costs = fields.Float("Costs")

    @api.depends("cargo_type")
    def _compute_get_cargo_type_ref(self):
        """Техническое поле, нужно для доменов"""

        for record in self:
            record.cargo_type_ref = record.cargo_type.ref

    service_type = fields.Many2one(
        "delivery_novaposhta.service_types", string="Service Types"
    )
    service_type_ref = fields.Char(
        compute="_compute_get_service_type_ref", help="Technical field"
    )

    @api.depends("service_type")
    def _compute_get_service_type_ref(self):
        for record in self:
            record.service_type_ref = record.service_type.ref

    datetime = fields.Date(string="Date")

    # sender info
    city_sender = fields.Many2one(
        "delivery_novaposhta.cities_list", string="Sender city"
    )
    sender_warehouse = fields.Many2one(
        "delivery_novaposhta.warehouse",
        domain="[('cityref', '=', city_ref)]",
        string="Sender Warehouse",
    )
    contact_sender = fields.Many2one(
        "delivery_novaposhta.sender_contact", string="Contact Person"
    )
    city_ref = fields.Char(compute="_compute_get_city_ref", help="Technical field")

    @api.depends("city_sender")
    def _compute_get_city_ref(self):
        """Техническое поле, нужно для доменов"""

        for record in self:
            record.city_ref = record.city_sender.ref

    # if organization
    recipient_name_organization = fields.Many2one(
        "res.partner",
        string="Recipient organization",
        domain="[('is_company','=',1)]",
    )
    # recipient info
    recipient_name = fields.Many2one(
        "res.partner",
        string="Recipient Name",
        domain="[('parent_id', '=', recipient_name_organization)]",
    )
    recipient_phone = fields.Char(string="Recipient Phone")
    streets = fields.Many2one("delivery_novaposhta.streets_list", string="Street")
    recipient_house = fields.Char(string="Recipient House")
    recipient_flat = fields.Integer(string="Recipient Flat")
    recipient_type = fields.Many2one(
        "delivery_novaposhta.types_of_counterparties", "Recipient Type"
    )
    recipient_type_ref = fields.Char(
        compute="_compute_get_rec_type_ref", help="Technical field"
    )

    @api.depends("recipient_type")
    def _compute_get_rec_type_ref(self):
        """Техническое поле, нужно для доменов"""

        for record in self:
            record.recipient_type_ref = record.recipient_type.ref

    recipient_city = fields.Many2one(
        "delivery_novaposhta.cities_list", string="Recipient City"
    )
    recipient_warehouse = fields.Many2one(
        "delivery_novaposhta.warehouse",
        domain="[('cityref', '=', rec_city_ref)]",
        string="Recipient Warehouse",
    )
    rec_city_ref = fields.Char(
        compute="_compute_get_rec_city_ref", help="Technical field"
    )

    @api.depends("recipient_city")
    def _compute_get_rec_city_ref(self):
        """Техническое поле, нужно для доменов"""

        for record in self:
            record.rec_city_ref = record.recipient_city.ref

    # product info
    seats_amount = fields.Integer(string="Seats amount")
    weight = fields.Float(string="Weight")

    @api.constrains("weight")
    def _check_weight(self):
        """Вес у документов может быть только 0.1, 0.5, 1"""

        for record in self:
            if (
                record.weight not in [0.1, 0.5, 1]
                and record.cargo_type.ref == "Documents"
            ):
                raise ValidationError(_("Documents can only have weight 0.1, 0.5, 1"))

    cost = fields.Monetary(string="Items Cost", currency_field="currency_id")
    currency_id = fields.Many2one(
        "res.currency",
        related="order_to_deliver.currency_id",
        string="Currency",
        readonly=True,
    )
    general_volume = fields.Float(string="General Volume")

    @api.constrains("general_volume")
    def _check_volume(self):
        """У документов и колес объем может быть только 0"""

        for record in self:
            if (
                record.cargo_type.ref in ("Documents", "TiresWheels")
                and record.general_volume != 0
            ):
                raise ValidationError(
                    _("For this cargo type general volume should be 0")
                )

    @api.onchange("cargo_type")
    def _cargo_type_change(self):
        """Фикс, бонус к _check_volume"""

        for record in self:
            if record.cargo_type.ref in ("Documents", "TiresWheels"):
                record.general_volume = 0

    wheels_type = fields.Many2one(
        "delivery_novaposhta.tires_wheels_list", string="Types of wheels"
    )
    amount = fields.Integer(string="Amount")

    def get_api_key(self):
        """Функция для получния ключа. Что б постоянно не писать"""

        try:
            return self.env["delivery_novaposhta.api_key"].search(
                [
                    ("active", "=", True),
                    ("company_id", "=", self.env.user.company_id.id),
                ]
            )[0]
        except IndexError as idx_error:
            raise ValidationError(_("There is no active API key!")) from idx_error

    def get_api_keys(self):
        """Функция для получния ключа. Что б постоянно не писать"""

        try:
            return self.env["delivery_novaposhta.api_key"].search(
                [("active", "=", True)]
            )
        except IndexError as idx_error:
            raise ValidationError(_("There is no active API key!")) from idx_error

    @api.onchange("order_to_deliver")
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
            cost = sum([ol.price_total for ol in order_line])
            currency_uah = self.env.ref("base.UAH")
            order_currency = record.order_to_deliver.currency_id
            if currency_uah != order_currency:
                cost = currency_uah.compute(cost, order_currency)
            record.cost = cost
            if record.seats_amount > 0:
                record.weight = (
                    sum(
                        [
                            (line.product_id.weight * line.product_uom_qty)
                            for line in order_line
                        ]
                    )
                    or 0.0
                )
                record.general_volume = (
                    sum(
                        [
                            (line.product_id.volume * line.product_uom_qty)
                            for line in order_line
                        ]
                    )
                    or 0.0
                )
            # recipient data
            record.recipient_type = record.order_to_deliver.partner_id.np_type
            if record.order_to_deliver.partner_id.np_type.ref == "Organization":
                record.recipient_name_organization = record.order_to_deliver.partner_id
            else:
                record.recipient_name = record.order_to_deliver.partner_id
            # salesperson
            record.salesperson = record.order_to_deliver.user_id

    @api.onchange("recipient_name")
    def _get_phone_from_recipient(self):
        for record in self:
            record.recipient_phone = record.recipient_name.mobile

    def add_privat_person(self):
        """Функция добавления контактного лица приватного лица

        'Приватна особа' сама по себе является контрагентом
        и у нее есть контактные лица, которые и есть народ,
        которому мы отправляем.
        """

        key = self.get_api_key()

        data = {
            "apiKey": key.key,
            "modelName": "Counterparty",
            "calledMethod": "getCounterparties",
            "methodProperties": {"CounterpartyProperty": "Recipient"},
        }
        try:
            response = APIRequest.get_data(data)
        except ConnectionError as conn_error:
            raise ValidationError(_("Connection Error")) from conn_error
        if isinstance(response, dict):
            raise ValidationError(
                _("Data was faulty:\n {response}").format(response=response)
            )

        # TODO: Not optimised...
        # Тут мутка для того, что б было удобней работать с респонсом
        # что б не пришлось по нему искать, я просто его рефакторю в удобный вид

        refactored_response = {
            record["CounterpartyType"]: record["Ref"]
            for record in response
            if record["CounterpartyType"] == "PrivatePerson"
        }
        first_name, last_name, middle_name = self.split_name()

        data = {
            "apiKey": key.key,
            "modelName": "ContactPerson",
            "calledMethod": "save",
            "methodProperties": {
                "CounterpartyRef": refactored_response["PrivatePerson"],
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
        return refactored_response["PrivatePerson"], response[0]["Ref"]

    def split_name(self):
        try:
            if (
                self.recipient_name.np_name
                and len(self.recipient_name.np_name.split()) > 2
            ):
                (
                    last_name,
                    first_name,
                    middle_name,
                ) = self.recipient_name.np_name.split()
            elif (
                self.recipient_name.np_name
                and len(self.recipient_name.np_name.split()) > 1
            ):
                last_name, first_name = self.recipient_name.np_name.split()
                middle_name = ""
            elif len(self.recipient_name.name.split()) > 2:
                (
                    last_name,
                    first_name,
                    middle_name,
                ) = self.recipient_name.name.split()
            elif len(self.recipient_name.name.split()) > 1:
                last_name, first_name = self.recipient_name.name.split()
                middle_name = ""
            else:
                raise ValidationError(_("Inappropriate name!"))
        except ValueError as value_error:
            raise ValidationError(_("Inappropriate name!")) from value_error
        return first_name, last_name, middle_name

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
                ###
                # TODO: тут не хватает кода ЕДРПОУ. Откуда его брать не понятно
                # в одном из проектов я использовал модуль kw_account_partner_requisites, откуда и брал
                # поле.
                # "EDRPOU": self.recipient_name_organization.enterprise_code,
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

    def save_address(self, x):
        """Изменить адрес.
        Пока useless функция, но оставлю - может пригодится
        {
        "apiKey": "YourApiKey",
        "modelName": "Address",
        "calledMethod": "save",
        "methodProperties": {
            "CounterpartyRef": "f53e834e-8d5e-11e7-8ba8-005056881c6b",
            "StreetRef": "bba0d9b3-4148-11dd-9198-001d60451983",
            "BuildingNumber": "45",
            "Flat": "12",
            "Note": "Комментарий"
            }
        }
        """
        key = self.get_api_key()

        data = {
            "apiKey": key.key,
            "modelName": "Address",
            "calledMethod": "save",
            "methodProperties": {
                "CounterpartyRef": x,
                "StreetRef": self.streets.ref,
                "BuildingNumber": self.recipient_house,
                "Flat": self.recipient_flat,
            },
        }

        response = APIRequest.get_data(data)
        return response[0]["Description"], response[0]["Ref"]

    @api.model
    def create(self, vals):
        """Один из самых потных кусков. Тут вся магия(почти)."""

        record = super().create(vals)
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
                "NewAddress": "1",
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
                "Weight": record.weight,
                "SeatsAmount": record.seats_amount,
                "Cost": cost,
                "VolumeGeneral": record.general_volume,
            },
        }

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

        if record.recipient_type.ref == "Organization":
            # "Отправка организации и ее контакному лицу"

            organization_ref, contact_person_ref = record.add_organization()
            if record.service_type.ref == "WarehouseDoors":
                data["methodProperties"].update(
                    {
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

        return record.send_ttn(data)

    def send_ttn(self, data):
        _logger.info("Data to send {data}".format(data=data))
        try:
            if not self._context.get("notif"):
                response = APIRequest.get_data(data)
            else:
                response = [
                    {
                        "IntDocNumber": "20450091402399",
                        "TypeDocument": "InternetDocument",
                        "CostOnSite": 25,
                        "TzoneName": "Тарифна зона: Тарифна зона 0 (0)",
                        "Ref": "a3d2735b-c109-11e8-8b24-005056881c6b",
                        "TzoneID": "00",
                        "EstimatedDeliveryDate": "06.10.2020",
                    }
                ]
        except ConnectionError as conn_error:
            raise ValidationError(_("Connection Error")) from conn_error
        if isinstance(response, dict):
            raise ValidationError(
                _("Data was faulty!\n {response}").format(response=response)
            )
        else:
            self.write(
                {
                    "doc_number": response[0]["IntDocNumber"],
                    "estimated_costs": response[0]["CostOnSite"],
                    "ref": response[0]["Ref"],
                    "estimated_delivery_date": datetime.strptime(
                        response[0]["EstimatedDeliveryDate"], "%d.%m.%Y"
                    ),
                }
            )
            self.update_status_one()
            _logger.info("Response: {response}".format(response=response))
        return self

    @api.model
    def _update_statuses(self):
        """
        1	Нова пошта очікує надходження від відправника
        2	Видалено
        3	Номер не знайдено
        4	Відправлення у місті ХХXХ.
        5	Відправлення прямує до міста YYYY.
        6	Відправлення у місті YYYY, орієнтовна доставка до ВІДДІЛЕННЯ-XXX dd-mm. Очікуйте додаткове повідомлення про прибуття.
        7	Прибув на відділення
        8	Прибув на відділення
        9	Відправлення отримано
        10	Відправлення отримано %DateReceived%. Протягом доби ви одержите SMS-повідомлення про надходження грошового переказу та зможете отримати його в касі відділення «Нова пошта».
        11	Відправлення отримано %DateReceived%. Грошовий переказ видано одержувачу.
        14	Відправлення передано до огляду отримувачу
        101	На шляху до одержувача
        102	Відмова одержувача
        103	Відмова одержувача
        108	Відмова одержувача
        104	Змінено адресу
        105	Припинено зберігання
        106	Одержано і є ТТН грошовий переказ
        107	Нараховується плата за зберігання
            {
                "apiKey": "[ВАШ КЛЮЧ]",
                "modelName": "TrackingDocument",
                "calledMethod": "getStatusDocuments",
                "methodProperties": {
                    "Documents": [
                        {
                            "DocumentNumber": "20400048799000",
                            "Phone":""
                        },
                        {
                            "DocumentNumber": "20400048799001",
                            "Phone":""
                        }
                    ]
                }
            }
        "data": [
            {
              "Number": "59000218530814",
              "Redelivery": 0,
              "RedeliverySum": 0,
              "RedeliveryNum": "",
              "RedeliveryPayer": "",
              "OwnerDocumentType": "",
              "LastCreatedOnTheBasisDocumentType": "",
              "LastCreatedOnTheBasisPayerType": "",
              "LastCreatedOnTheBasisDateTime": "",
              "LastTransactionStatusGM": "",
              "LastTransactionDateTimeGM": "",
              "DateCreated": "18-11-2016 11:52:42",
              "DocumentWeight": 0.5,
              "CheckWeight": 0,
              "DocumentCost": 20,
              "SumBeforeCheckWeight": 0,
              "PayerType": "Recipient",
              "RecipientFullName": "ФИО",
              "RecipientDateTime": "21.11.2016 13:53:47",
              "ScheduledDeliveryDate": "19-11-2016",
              "PaymentMethod": "Cash",
              "CargoDescriptionString": "Одяг",
              "CargoType": "Cargo",
              "CitySender": "Київ",
              "CityRecipient": "Київ",
              "WarehouseRecipient": "Відділення №101 (до 15 кг), Міні-відділення: вул. Велика Васильківська, 143/2, (маг. \"Фора\")",
              "CounterpartyType": "PrivatePerson",
              "AfterpaymentOnGoodsCost": 0,
              "ServiceType": "WarehouseWarehouse",
              "UndeliveryReasonsSubtypeDescription": "",
              "WarehouseRecipientNumber": 101,
              "LastCreatedOnTheBasisNumber": "",
              "PhoneRecipient": "380ХХХХХХХХХ",
              "RecipientFullNameEW": "ФИО",
              "WarehouseRecipientInternetAddressRef": "39931b02-e1c2-11e3-8c4a-0050568002cf",
              "MarketplacePartnerToken": "",
              "ClientBarcode": "",
              "RecipientAddress": "м. Київ, Відділення №101 (до 15 кг), Міні-відділення, вул. Велика Васильківська, 143/2",
              "CounterpartyRecipientDescription": "Приватна особа",
              "CounterpartySenderType": "PrivatePerson",
              "DateScan": "0001-01-01 00:00:00",
              "PaymentStatus": "",
              "PaymentStatusDate": "",
              "AmountToPay": "",
              "AmountPaid": "",
              "Status": "Одержано",
              "StatusCode": "9",
              "RefEW": "55fbe203-ad74-11e6-b5da-005056887b8d",
              "BackwardDeliverySubTypesServices": [],
              "BackwardDeliverySubTypesActions": [],
              "UndeliveryReasons": ""
            }
          ],
        """
        key = self.get_api_key()

        # """ Выбираем ЭН статусы которых не входят в пул,
        # чтобы не делать лишних запросов.
        # """
        # TODO: Эту же проверку можно сделать внутри домена. Надо переделать. Будет меньше на бд нагруз

        ttns_to_check = [
            record
            for record in self.search([("status_code", "not in", TTN_IGNORE_STATUS)])
        ]
        i = 0

        while i < len(ttns_to_check):
            ttns_to_check_part = ttns_to_check[i : i + 50]
            i += 50
            # """ тут спрятан компрехеншн :3 """
            data = {
                "apiKey": key.key,
                "modelName": "TrackingDocument",
                "calledMethod": "getStatusDocuments",
                "methodProperties": {
                    "Documents": [
                        {"DocumentNumber": ttn.doc_number, "Phone": ""}
                        for ttn in ttns_to_check_part
                    ]
                },
            }
            _logger.debug(_("Data to send: {}").format(data))
            try:
                response = APIRequest.get_data(data)
            except ConnectionError as conn_error:
                raise ValidationError(_("Connection Error")) from conn_error
            _logger.debug(_("Response: {}").format(response))
            if isinstance(response, dict):
                return
            else:
                # """Если найдены ЭН для обновления, смотрим их статусы из респонса"""

                response_transformed = {
                    record["Number"]: [record["Status"], record["StatusCode"]]
                    for record in response
                }
                for ttn in ttns_to_check_part:
                    if ttn.doc_number and ttn.status_code != int(
                        response_transformed[ttn.doc_number][1]
                    ):
                        ttn.write(
                            {
                                "status": response_transformed[ttn.doc_number][0],
                                "status_code": response_transformed[ttn.doc_number][1],
                            }
                        )

                        # """ Высылаем уведомления продажнику этой ЭН """

                        if (
                            int(response_transformed[ttn.doc_number][1])
                            in TTN_NOTIFY_STATUS
                        ):
                            ttn.salesperson.notify_info(
                                _("TTN {ttn} changed status to {status}").format(
                                    ttn=ttn.doc_number,
                                    status=response_transformed[ttn.doc_number][0],
                                ),
                                sticky=True,
                            )
                        elif int(response_transformed[ttn.doc_number][1]) == 2:
                            ttn.salesperson.notify_warning(
                                _("TTN {ttn} changed status to {status}").format(
                                    ttn=ttn.doc_number,
                                    status=response_transformed[ttn.doc_number][0],
                                ),
                                sticky=True,
                            )

    def update_status_one(self):
        self.ensure_one()

        # """ Вызывается кнопкой на форме ЭН. Обновляет статус этой ЭН """

        key = self.get_api_key()

        data = {
            "apiKey": key.key,
            "modelName": "TrackingDocument",
            "calledMethod": "getStatusDocuments",
            "methodProperties": {
                "Documents": [{"DocumentNumber": self.doc_number, "Phone": ""}]
            },
        }

        try:
            response = APIRequest.get_data(data)
        except ConnectionError as conn_error:
            raise ValidationError(_("Connection Error")) from conn_error
        if self.status_code != int(response[0]["StatusCode"]):
            self.with_context(no_update_np=True).write(
                {
                    "status": response[0]["Status"],
                    "status_code": response[0]["StatusCode"],
                }
            )
            if int(response[0]["StatusCode"]) in (
                9,
                11,
                102,
                103,
                108,
                105,
                106,
                107,
            ):
                self.salesperson.notify_info(
                    _("TTN {ttn} changed status to {status}").format(
                        ttn=self.doc_number, status=response[0]["Status"]
                    ),
                    sticky=True,
                )
            elif int(response[0]["StatusCode"]) == 2:
                self.salesperson.notify_warning(
                    _("TTN {ttn} changed status to {status}").format(
                        ttn=self.doc_number, status=response[0]["Status"]
                    ),
                    sticky=True,
                )
        return True

    def write(self, vals):
        if (
            self._context.get("no_update_np")
            or self._context.get("autocreate")
            or all(field in vals.keys() for field in ["status", "status_code"])
        ):
            # this is status update or create
            return super().write(vals)
        else:
            # this is save
            key = self.get_api_key()

            data = {
                "apiKey": key.key,
                "modelName": "InternetDocument",
                "calledMethod": "update",
                "methodProperties": {
                    "Sender": key.senderref,
                    "DateTime": date_to_str(vals.get("datetime"))
                    or date_to_str(self.datetime),
                },
            }
            ttn_list = [
                "Ref",
                "Description",
                "PayerType",
                "PaymentMethod",
                "CargoType",
                "ServiceType",
                "CitySender",
                "SenderAddress",
                "ContactSender",
                "SendersPhone",
                "CityRecipient",
                "RecipientAddress",
                "RecipientsPhone",
                "Weight",
                "SeatsAmount",
                "Cost",
                "VolumeGeneral",
            ]
            data["methodProperties"].update(get_value(self, vals, ttn_fields, ttn_list))

            if self.order_to_deliver.backward_money or vals.get("backward_money"):
                data["methodProperties"].update(
                    {
                        "BackwardDeliveryData": [
                            get_value(
                                self,
                                vals,
                                backward_field,
                                ["PayerType", "RedeliveryString"],
                            )
                        ]
                    }
                )
                data["methodProperties"]["BackwardDeliveryData"][0].update(
                    {"CargoType": "Money"}
                )

            if data["methodProperties"]["CargoType"] == "TiresWheels":
                data["methodProperties"].update(
                    {
                        "CargoDetails": [
                            {
                                "CargoDescription": self.wheels_type.ref,
                                "Amount": self.amount,
                            }
                        ],
                        "SeatsAmount": self.amount,
                    }
                )
                self.with_context(no_update_np=True).write(
                    {
                        "seatsamount": self.amount,
                    }
                )
            elif self.cargo_type.ref == "Pallet":
                raise ValidationError(_("Pallets are bugged and not working"))

            if vals.get("recipienttype"):
                recipienttype = self.recipient_type.browse(
                    vals.get("recipienttype")
                ).ref
            else:
                recipienttype = self.recipient_type.ref
            if recipienttype == "PrivatePerson":
                (
                    private_person_ref,
                    contact_person_ref,
                ) = self.add_privat_person()
                data["methodProperties"].update(
                    {
                        "Recipient": private_person_ref,
                        "ContactRecipient": contact_person_ref,
                    }
                )
                try:
                    response = APIRequest.send_data(data)
                except ConnectionError:
                    return ValidationError(_("ConnectionError"))
                if isinstance(response, dict):
                    raise ValidationError(
                        _("Data was faulty!:\n {response}").format(response=response)
                    )
                vals.update(
                    {
                        "estimated_costs": response[0]["CostOnSite"],
                        "estimated_delivery_date": datetime.strptime(
                            response[0]["EstimatedDeliveryDate"], "%d.%m.%Y"
                        ),
                    }
                )
            else:
                organization_ref, contact_person_ref = self.add_privat_person()
                data["methodProperties"].update(
                    {
                        "Recipient": organization_ref,
                        "ContactRecipient": contact_person_ref,
                    }
                )
                try:
                    response = APIRequest.send_data(data)
                except ConnectionError:
                    return ValidationError(_("ConnectionError"))
                if isinstance(response, dict):
                    raise ValidationError(
                        _("Data was faulty!:\n {response}").format(response=response)
                    )
                vals.update(
                    {
                        "estimated_costs": response[0]["CostOnSite"],
                        "estimated_delivery_date": datetime.strptime(
                            response[0]["EstimatedDeliveryDate"], "%d.%m.%Y"
                        ),
                    }
                )
            return super().write(vals)

    def delete_one(self):
        """Вызывается по кнопке на форме. Отправляет НП инфу,
        что данная ТТН должна быть удалена.
        Не удаляет ЭН у нас из базы.
        """

        self.ensure_one()

        key = self.get_api_key()

        data = {
            "apiKey": key.key,
            "modelName": "InternetDocument",
            "calledMethod": "delete",
            "methodProperties": {"DocumentRefs": self.ref},
        }

        _logger.debug(_("Data to send: {data}").format(data=data))
        try:
            response = APIRequest.get_data(data)
        except ConnectionError as conn_error:
            raise ValidationError(_("Connection Error")) from conn_error
        _logger.debug(_("Response: {response}").format(response=response))

        self.update_status_one()

        return True

    def unlink(self):
        """Отправляет в НП данные об удалении при удалении ЭН у нас из базы"""

        # self.delete_one()
        return super().unlink()

    def new_ttn(self, data_dict):
        res = {}
        for key, value in data_dict.items():
            if key in ttn_fields:
                if len(ttn_fields[key]) == 2:
                    env = self[ttn_fields[key][0]]
                    r = env.search([(ttn_fields[key][1], "=", value)])
                    if r:
                        if len(r) == 1:
                            val = r.id
                    else:
                        val = env.create({ttn_fields[key][1]: value}).id
                elif len(ttn_fields[key]) == 1:
                    val = value
                else:
                    continue
                res[ttn_fields[key][0]] = val
        partner_env = self.env["res.partner"]
        domain = [
            "|",
            "|",
            "|",
            ("np_ref", "=", data_dict["ContactRecipient"]),
            ("phone", "=", data_dict["RecipientContactPhone"]),
            ("mobile", "=", data_dict["RecipientContactPhone"]),
            ("name", "=", data_dict["RecipientContactPerson"]),
        ]
        partner = partner_env.search(domain, limit=1)
        if partner:
            res["recipient_name"] = partner.id
        else:
            res["recipient_name"] = partner_env.create(
                {
                    "name": data_dict["RecipientContactPerson"],
                    "np_ref": data_dict["ContactRecipient"],
                    "phone": data_dict["RecipientContactPhone"],
                    "city": data_dict["CitySenderDescription"],
                }
            ).id
        return self.with_context(create=True).create(res)

    def print_document(self):
        key = self.get_api_key()
        url = (
            "https://my.novaposhta.ua/orders/printDocument/orders[]/"
            + self.ref
            + "/type/html/apiKey/"
            + key.key
        )
        return {
            "name": _("TTN"),
            "type": "ir.actions.act_url",
            "url": url,
            "target": "new",
        }

    def print_document_pdf(self):
        key = self.get_api_key()
        url = (
            "https://my.novaposhta.ua/orders/printDocument/orders[]/"
            + self.ref
            + "/type/pdf/apiKey/"
            + key.key
        )
        return {
            "name": _("TTN"),
            "type": "ir.actions.act_url",
            "url": url,
            "target": "new",
        }

    def print_barcode(self):
        key = self.get_api_key()
        url = (
            "https://my.novaposhta.ua/orders/printMarkings/orders[]/"
            + self.ref
            + "/type/html/apiKey/"
            + key.key
        )

        return {
            "name": _("TTN"),
            "type": "ir.actions.act_url",
            "url": url,
            "target": "new",
        }

    def print_barcode_pdf(self):
        key = self.get_api_key()
        url = (
            "https://my.novaposhta.ua/orders/printMarkings/orders[]/"
            + self.ref
            + "/type/pdf/apiKey/"
            + key.key
        )
        return {
            "name": _("TTN"),
            "type": "ir.actions.act_url",
            "url": url,
            "target": "new",
        }

    def get_url_ttn(self):
        url = "https://novaposhta.ua/tracking/?cargo_number=%s" % self.doc_number
        return {
            "name": _("TTN"),
            "type": "ir.actions.act_url",
            "url": url,
            "target": "new",
        }


class SyncTTN(models.TransientModel):
    _name = "delivery_novaposhta.sync_ttn"

    date_from = fields.Date("Date from")
    date_to = fields.Date("Date to")

    def synchronize(self):
        try:
            keys = self.env["delivery_novaposhta.api_key"].search(
                [("active", "=", True)]
            )
        except IndexError as idx_error:
            raise ValidationError(_("There is no active API key!")) from idx_error
        for key in keys:
            data = {
                "apiKey": key.key,
                "modelName": "InternetDocument",
                "calledMethod": "getDocumentList",
                "methodProperties": {"GetFullList": "1"},
            }
            ctx = self._context
            date_from = (
                date_to_str(self.date_from) if self.date_from else ctx.get("date_from")
            )
            date_to = date_to_str(self.date_to) if self.date_to else ctx.get("date_to")
            if date_from and date_to:
                date = {
                    "DateTimeFrom": date_from or datetime.now().strftime("%d.%m.%Y"),
                    "DateTimeTo": date_to or datetime.now().strftime("%d.%m.%Y"),
                }
            else:
                date = {
                    "DateTime": date_from
                    or date_to
                    or datetime.now().strftime("%d.%m.%Y"),
                }
            data["methodProperties"].update(date)
            try:
                response = APIRequest.get_data(data)
            except ConnectionError as conn_error:
                raise ValidationError(_("Connection Error")) from conn_error
            _logger.debug(_("Response: {response}").format(response=response))
            if response:
                ttn_env = self.env["delivery_novaposhta.ttn"]
                ttn_list = [r.doc_number for r in ttn_env.search([])]
                for r in response:
                    if r["IntDocNumber"] not in ttn_list:
                        r["company_id"] = key.company_id.id
                        ttn_env.new_ttn(r)


def get_value(record, vals, field_dict, field_list, gv=False):
    res = {}
    for field in field_list:
        if field in field_dict and field_dict[field]:
            field_in_vals = field_dict[field][0]
            if field_in_vals in vals:
                value = vals[field_in_vals]
                if len(field_dict[field]) != 1:
                    value = record[field_in_vals].browse(vals[field_in_vals])
                    for v in field_dict[field][1:]:
                        value = value[v]
            else:
                value = record[field_in_vals]
                if len(field_dict[field]) != 1:
                    for v in field_dict[field][1:]:
                        value = value[v]
            res[field] = value
    if gv:
        return value
    return res
