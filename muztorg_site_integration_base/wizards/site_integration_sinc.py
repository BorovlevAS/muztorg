import logging
from datetime import datetime

import xml2dict

from odoo import _, fields, models

from odoo.addons.phone_validation.tools import phone_validation

from ..muztorg_api.api import MTApi

# import XML2Dict
# from encoder import XML2Dict
# import muztorg_site_integration_base.muztorg_api.xml2dict as xml2dict


# import XML2Dict


_logger = logging.getLogger(__name__)

# from odoo import http


class SiteIntegrationSync(models.TransientModel):
    _name = "site.integration.sync"
    _description = "Site-integration Sync client"

    settings_id = fields.Many2one("site.integration.base")
    url = fields.Char()
    protocol_id = fields.Many2one("site.integration.protocol")

    def _get_rest_endpoint(self, website, **kwargs):
        return ""

    def import_data(self):
        value_protocol = {
            "note": "",
            "date_exchange": datetime.today(),
            "settings_id": self.settings_id.id,
        }
        protocol = self.env["site.integration.protocol"].sudo()
        # id =  protocol.create(value_protocol)
        self.protocol_id = protocol.create(value_protocol)

        try:
            # Загрузка файла с сайта
            API = MTApi(self.url, "")  # self._get_rest_endpoint(website, **kwargs)
            response = API.import_data()
            if response:
                data = response.content.decode("utf-8")
                self.protocol_id.create_file(response.content)
                dict_reply = xml2dict.parse(data)
                self.protocol_id.status = "ok"
                return self.import_orders(dict_reply)
            else:
                _logger.exception(
                    "Failed to download file with setting %s", self.settings_id.name
                )
                self.protocol_id.note = self.protocol_id.note + _(
                    "\nNo access to the site "
                )
                self.protocol_id.status = "error"
                return False
        except Exception as exc:
            _logger.exception("exception: %s", exc)
            self.protocol_id.note = self.protocol_id.note + _("\nexception: %s", exc)
            self.protocol_id.status = "error"

    def import_orders(self, dict_reply):
        if not dict_reply.get("orders"):
            for ind in dict_reply:
                if dict_reply[ind].get("orders"):
                    so_count = self.load_data(dict_reply[ind].get("orders"))

        _logger.exception("%s orders loaded", so_count)
        self.protocol_id.note = self.protocol_id.note + _(
            "\n%s orders loaded", so_count
        )

        return True

    def load_data(self, data):
        count = 0
        for order in data.get("order"):
            res = self.load_order(order)
            if res:
                count += 1

        return count

    def get_partner(self, value_partner, value_address):
        def format_phone(number):
            if not number:
                return False

            country = self.env.ref("base.ua")
            if not country:
                return number
            return phone_validation.phone_format(
                number,
                country.code if country else None,
                country.phone_code if country else None,
                force_format="INTERNATIONAL",
                raise_exception=False,
            )

        def search_address(partner, value_address):
            # city, warehouse, street=None
            shipping = value_address.get("shipping")
            if shipping != "NOVA POSHTA":
                return False

            city_str = value_address.get("city")
            city_ref = value_address.get("city_ref")
            address_str = value_address.get("address")
            warehouse_ref = value_address.get("warehouse")

            CitiesList = self.env["delivery_novaposhta.cities_list"].sudo()
            city = CitiesList.search([("ref", "=", city_ref)], limit=1)
            if not city:
                _logger.info("city not found %s", city_str)
                self.protocol_id.note = self.protocol_id.note + _(
                    "\nDelivery city not found  %s", city_str
                )
                return partner

            if warehouse_ref:
                WarehouseNP = self.env["delivery_novaposhta.warehouse"].sudo()
                warehouse = WarehouseNP.search([("ref", "=", warehouse_ref)], limit=1)
                if not warehouse:
                    self.protocol_id.note = self.protocol_id.note + _(
                        "\nDelivery branch not found %s", warehouse_ref
                    )
            else:
                warehouse = None
            street = self.env["delivery_novaposhta.streets_list"]
            if address_str and not warehouse_ref:
                streer_str = address_str.split(",")[0]
                StreetNP = self.env["delivery_novaposhta.streets_list"].sudo()
                street = StreetNP.search(
                    [("city_id", "=", city.id), ("name", "=", streer_str)], limit=1
                )
                _logger.info("street not found %s", streer_str)
                self.protocol_id.note = self.protocol_id.note + _(
                    "\nDelivery street not found %s", streer_str
                )
                return partner

            Partner = self.env["res.partner"].sudo()
            partner_domain = [
                ("parent_id", "=", partner.id),
                ("type", "=", "delivery"),  # Тип адреси	Адреса доставки
                ("np_delivery_address", "=", True),  # Адреса для Нової Пошти
                ("np_city", "=", city.id),
            ]
            # np_service_type 1		Doors	Адреса 2		Warehouse	Склад Тип послуги
            if warehouse:
                partner_domain.append(("np_warehouse", "=", warehouse.id))
                partner_domain.append(("np_service_type", "=", "Warehouse"))
            elif street:
                partner_domain.append(("np_street", "=", street.id))
                partner_domain.append(("np_service_type", "=", "Doors"))

            partner_address = Partner.search(partner_domain, limit=1)

            if partner_address:
                return partner_address
            else:
                return partner

        def search_partner(phone, email, lastname, firstname, value_address):
            # Partner = self.env["res.partner"].with_company(company.id).sudo()
            Partner = self.env["res.partner"].sudo()

            partner_domain = [
                "|",
                ("mobile", "=", phone),
                ("biko_1c_phone", "=", phone),
            ]
            partner = Partner.search(partner_domain, limit=1)

            if partner:
                address = search_address(partner, value_address)
                return partner, address

            partner_domain = [
                ("email", "=", email),
            ]
            partner = Partner.search(partner_domain, limit=1)

            if partner:
                address = search_address(partner, value_address)
                return partner, address

            data = {
                "lastname": lastname,
                "firstname": firstname,
                "mobile": phone,
                "email": email,
                "country_id": self.env.ref("base.ua").id,
                "type": "contact",
                "lang": self.env.lang,
            }
            _logger.info("create a partner %s", lastname)
            self.protocol_id.note = self.protocol_id.note + _(
                "\ncreate a partner %s", lastname
            )
            partner = Partner.create(data)

            if not partner:
                self.protocol_id.note = self.protocol_id.note + _(
                    "\nIt is impossible to register a client %s",
                    lastname + " " + firstname,
                )

            # shipping = value_address.get("shipping")
            # if shipping != "NOVA POSHTA":
            #     return partner, False

            # city_str = value_address.get("city")
            # city_ref = value_address.get("city_ref")
            # address_str = value_address.get("address")
            # warehouse_ref = value_address.get("warehouse")

            # CitiesList = self.env["delivery_novaposhta.cities_list"].sudo()
            # city = CitiesList.search([("ref", "=", city_ref)], limit=1)
            # if not city:
            #     _logger.info("city not found %s", city_str)
            #     self.protocol_id.note = self.protocol_id.note + _(
            #         "\ncity not found %s", city_str
            #     )
            #     return partner, partner

            # if warehouse_ref:
            #     WarehouseNP = self.env["delivery_novaposhta.warehouse"].sudo()
            #     warehouse = WarehouseNP.search(
            #         [("ref", "=", warehouse_ref)], limit=1
            #     )
            # else:
            #     warehouse = None
            # street = self.env["delivery_novaposhta.streets_list"]
            # if address_str and not warehouse_ref:
            #     streer_str = address_str.split(",")[0]
            #     StreetNP = self.env["delivery_novaposhta.streets_list"].sudo()
            #     street = StreetNP.search(
            #         [("city_id", "=", city.id), ("name", "=", streer_str)], limit=1
            #     )
            #     # если не нашли улицу, то возвращаем самого партнера, т.к это поле обязательное
            #     if not street:
            #         _logger.info("street not found %s", streer_str)
            #         self.protocol_id.note = self.protocol_id.note + _(
            #             "\nstreet not found %s", streer_str
            #         )

            #             return partner, partner

            # Partner = self.env["res.partner"].sudo()
            # data = {
            #     "country_id": self.env.ref("base.ua").id,
            #     "type": "delivery",
            #     "lang": self.env.lang,
            #     "parent_id": partner.id,
            #     "np_delivery_address": True,
            #     "np_city": city.id,
            # }

            # # np_service_type 1		Doors	Адреса 2		Warehouse	Склад Тип послуги
            # if warehouse:
            #     data["np_warehouse"] = warehouse.id
            #     data["np_service_type"] = "Warehouse"
            # elif street:
            #     data["lastname"] = streer_str
            #     data["np_street"] = street.id
            #     data["np_service_type"] = "Doors"
            #     data["house"] = address_str.split(",")[1]
            # partner_address = Partner.create(data)

            partner_address = search_address(partner, value_address)
            return partner, partner_address

        phone_code = value_partner.get("phone_code")
        telephone = value_partner.get("telephone")
        email = value_partner.get("email")
        lastname = value_partner.get("lastname")
        firstname = value_partner.get("firstname")
        patronymic = value_partner.get("patronymic")
        _logger.info("-----------------search for a partner %s", lastname)
        phone = format_phone(phone_code + telephone)

        if patronymic:
            firstname = firstname + " " + patronymic

        return search_partner(phone, email, lastname, firstname, value_address)

    def load_order(self, data_order):
        def get_so_line(so, product_dict):
            product = self.env["product.product"].search(
                [
                    ("biko_control_code", "=", product_dict.get("product_id")),
                ]
            )
            # product_tmp = self.env["product.template"].search(
            #     [
            #         ("biko_control_code", "=", product_dict.get('product_id')),
            #     ]
            # )
            if product:
                str_values = {
                    "order_id": so.id,
                    "product_id": product.id,
                    "product_template_id": product.product_tmpl_id.id,
                    "product_uom_qty": product_dict.get("quantity", None),
                    # "price_unit": product_dict.get('price', None),
                }

                order_line = self.env["sale.order.line"].create(str_values)
                order_line.product_id_change()
                order_line.price_unit = product_dict.get("price", order_line.price_unit)
                return False
            else:
                self.protocol_id.note = self.protocol_id.note + _(
                    "\nProduct not found by control code  %s",
                    product_dict.get("product_id"),
                )
                return True

        if not data_order.get("order_id"):
            return False

        so = self.env["sale.order"].search(
            [("biko_website_ref", "=", data_order.get("order_id"))]
        )
        if so:
            #  уже загружен, пропускаем
            _logger.info("the order is already loaded %s", so)
            self.protocol_id.note = self.protocol_id.note + _(
                "\nthe order is already loaded #%s", data_order.get("order_id")
            )
            return False

        self.protocol_id.note = self.protocol_id.note + _(
            "\nLoading order #%s", data_order.get("order_id")
        )
        shipping = data_order.get("shipping", None)
        order_id = data_order.get("order_id", None)

        value_partner = {
            "phone_code": data_order.get("phone_code", None),
            "telephone": data_order.get("telephone", None),
            "email": data_order.get("email", None),
            "lastname": data_order.get("lastname", None),
            "firstname": data_order.get("firstname", None),
            "patronymic": data_order.get("patronymic", None),
        }
        value_address = {
            "city": data_order.get("city", None),
            "city_ref": data_order.get("city_ref", None),
            "address": data_order.get("address", None),
            "warehouse": data_order.get("warehouse", None),
            "shipping": shipping,
        }

        partner, address = self.get_partner(value_partner, value_address)

        pricelist_value = (
            self.env["site.integration.setting.line"]
            .search(
                [
                    ("settings_id", "=", self.settings_id.id),
                    ("id_seting", "=", "id_prajs"),
                ]
            )
            .value_many2one
        )

        payment_type = self.env["so.payment.type"].search(
            [("website_ref", "=", data_order.get("payment", None))], limit=1
        )
        if not payment_type:
            self.protocol_id.note = self.protocol_id.note + _(
                "\nFailed to select payment type %s", data_order.get("payment", None)
            )

        # carrier_id	Способ доставки - если shipping = 'NOVA POSHTA', то это Новая почта, если SamovyvozMTPodol - самовывоз
        # склад
        # warehouse_id	Склад отгрузки определяем так: если shipping = 'NOVA POSHTA', то это всегда склад головний,
        # если SamovyvozMTPodol, то это склад подол
        if shipping == "NOVA POSHTA":
            carrier_value = (
                self.env["site.integration.setting.line"]
                .search(
                    [
                        ("settings_id", "=", self.settings_id.id),
                        ("id_seting", "=", "id_nova_poshta"),
                    ]
                )
                .value_many2one
            )
            warehouse_value = (
                self.env["site.integration.setting.line"]
                .search(
                    [
                        ("settings_id", "=", self.settings_id.id),
                        ("id_seting", "=", "id_sklad_holovnyj"),
                    ]
                )
                .value_many2one
            )

        else:
            carrier_value = (
                self.env["site.integration.setting.line"]
                .search(
                    [
                        ("settings_id", "=", self.settings_id.id),
                        ("id_seting", "=", "id_samovyviz"),
                    ]
                )
                .value_many2one
            )
            warehouse_value = (
                self.env["site.integration.setting.line"]
                .search(
                    [
                        ("settings_id", "=", self.settings_id.id),
                        ("id_seting", "=", "id_sklad_podil"),
                    ]
                )
                .value_many2one
            )
        # afterpayment_check	если способ доставки Новая почта и способ payment = PriPoluchenii, то True, иначе False
        afterpayment_check = (
            True
            if shipping == "NOVA POSHTA"
            and data_order.get("payment") == "PriPoluchenii"
            else False
        )

        # note	Комментарий. Нужно составить строку #Заказ з сайту.
        # Номер: <номер_заказа>. Доставка: <что_там_нашли> <куда_отправляем> и контакты клиента

        order_id = data_order.get("order_id")

        note = f"Номер: {order_id}. Доставка: {shipping} {data_order.get('address')} {partner.mobile} {partner.email}"
        if data_order.get("comment"):
            note = data_order.get("comment") + " " + note

        so_values = {
            "partner_id": partner.id,
            "biko_contact_person_type": "person",
            "biko_contact_person_id": partner.id,
            "biko_recipient_id": partner.id,
            "biko_recipient_type": "person",
            "biko_website_ref": data_order.get("order_id"),
            "date_order": datetime.strptime(
                data_order.get("order_date"), "%Y-%m-%d %H:%M:%S"
            ),
            "afterpayment_check": afterpayment_check,
            "note": note,
            "so_payment_type_id": payment_type.id,
        }
        if carrier_value:
            so_values["carrier_id"] = carrier_value.id
        if pricelist_value:
            so_values["pricelist_id"] = pricelist_value.id

        if address:
            so_values["partner_shipping_id"] = address.id
        if warehouse_value:
            so_values["warehouse_id"] = warehouse_value.id
        so = self.env["sale.order"].create(so_values)

        #  ТЧ Продукты
        products = data_order.get("products", False)
        is_error = False
        if products:
            product = products["product"]
            if isinstance(product, dict):
                is_error += get_so_line(so, product)
            else:
                for product_dict in product:
                    is_error += get_so_line(so, product_dict)

        if len(so.order_line) != 0 and not is_error:
            if data_order.get("payment") == "PriPoluchenii":
                so.action_confirm()
            else:
                so.action_set_waiting()
        else:
            self.protocol_id.note = self.protocol_id.note + _(
                "\nThe order has not been confirmed and is recorded with number  %s",
                so.name,
            )

        # Если в настройке установлен признак Создавать лиды/сделки, то нужно создавать еще и их (модель crm.lead).
        if self.settings_id.is_create_leads:
            self.create_lead(so)

        return True

    def create_lead(self, so):
        team_value = (
            self.env["site.integration.setting.line"]
            .search(
                [
                    ("settings_id", "=", self.settings_id.id),
                    ("id_seting", "=", "id_komanda_prodazhu"),
                ]
            )
            .value_many2one
        )
        stage_value = (
            self.env["site.integration.setting.line"]
            .search(
                [
                    ("settings_id", "=", self.settings_id.id),
                    ("id_seting", "=", "id_etap"),
                ]
            )
            .value_many2one
        )

        lead_values = {
            "team_id": team_value.id,
            "stage_id": stage_value.id,
            "type": "opportunity",
            "name": so.partner_id.name,
            "expected_revenue": so.amount_total,
            "partner_id": so.partner_id.id,
            "contact_name": so.partner_id.firstname,
            "contact_lastname": so.partner_id.lastname,
            "mobile": so.partner_id.mobile,
        }
        lead = self.env["crm.lead"].create(lead_values)
        so.opportunity_id = lead.id

        for line in so.order_line:
            str_values = {
                "lead_id": lead.id,
                "product_id": line.product_id.id,
                "description": line.name,
                "qty": line.product_uom_qty,
                "product_uom": line.product_uom.id,
                "price_unit": line.price_unit,
                "tax_id": line.tax_id,
            }
            # new_line = new_lines.new(data)
            # new_lines += new_line
            # lead.lead_product_ids += new_lines
            self.env["crm.lead.product"].create(str_values)
