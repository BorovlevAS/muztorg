import logging

import xml2dict

from odoo import fields, models

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

    def _get_rest_endpoint(self, website, **kwargs):
        return ""

    def import_data(self):
        # Загрузка файла с сайта
        API = MTApi(self.url, "")  # self._get_rest_endpoint(website, **kwargs)
        response = API.import_data()
        if response:
            data = response.content.decode("utf-8")
            dict_reply = xml2dict.parse(data)
            # print(dict)

            if not dict_reply.get("orders"):
                for ind in dict_reply:
                    if dict_reply[ind].get("orders"):
                        so_count = self.load_data(dict_reply[ind].get("orders"))

            _logger.exception("%s orders loaded", so_count)

            return True
        else:
            # print("Failed to download file")
            _logger.exception("Failed to download file")
            return False

    def load_data(self, data):
        count = 0
        for order in data.get("order"):
            res = self.load_order(order)
            if res:
                count += 1

        return count

    def load_order(self, data_order):
        def get_partner(value_partner, value_address):
            # phone_code, telephone, email, lastname, firstname, patronymic
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
                    return False

                if warehouse_ref:
                    WarehouseNP = self.env["delivery_novaposhta.warehouse"].sudo()
                    warehouse = WarehouseNP.search(
                        [("ref", "=", warehouse_ref)], limit=1
                    )
                street = self.env["delivery_novaposhta.streets_list"]
                if address_str and not warehouse_ref:
                    streer_str = address_str.split(",")[0]
                    StreetNP = self.env["delivery_novaposhta.streets_list"].sudo()
                    street = StreetNP.search(
                        [("city_id", "=", city.id), ("name", "=", streer_str)], limit=1
                    )

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
                partner = Partner.create(data)

                shipping = value_address.get("shipping")
                if shipping != "NOVA POSHTA":
                    return partner, False

                city_str = value_address.get("city")
                city_ref = value_address.get("city_ref")
                address_str = value_address.get("address")
                warehouse_ref = value_address.get("warehouse")

                CitiesList = self.env["delivery_novaposhta.cities_list"].sudo()
                city = CitiesList.search([("ref", "=", city_ref)], limit=1)
                if not city:
                    _logger.info("city not found %s", city_str)
                    return partner, partner

                if warehouse_ref:
                    WarehouseNP = self.env["delivery_novaposhta.warehouse"].sudo()
                    warehouse = WarehouseNP.search(
                        [("ref", "=", warehouse_ref)], limit=1
                    )
                street = self.env["delivery_novaposhta.streets_list"]
                if address_str and not warehouse_ref:
                    streer_str = address_str.split(",")[0]
                    StreetNP = self.env["delivery_novaposhta.streets_list"].sudo()
                    street = StreetNP.search(
                        [("city_id", "=", city.id), ("name", "=", streer_str)], limit=1
                    )

                Partner = self.env["res.partner"].sudo()
                data = {
                    "mobile": phone,
                    "email": email,
                    "country_id": self.env.ref("base.ua").id,
                    "type": "delivery",
                    "lang": self.env.lang,
                    "parent_id": partner.id,
                    "np_delivery_address": True,
                    "np_city": city.id,
                }

                # np_service_type 1		Doors	Адреса 2		Warehouse	Склад Тип послуги
                if warehouse:
                    data["np_warehouse"] = warehouse.id
                    data["np_service_type"] = "Warehouse"
                elif street:
                    data["lastname"] = streer_str
                    data["np_street"] = street.id
                    data["np_service_type"] = "Doors"
                    data["house"] = address_str.split(",")[1]
                partner_address = Partner.create(data)

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

        if not data_order.get("order_id"):
            return False

        so = self.env["sale.order"].search(
            [("biko_website_ref", "=", data_order.get("order_id"))]
        )
        if so:
            #  уже загружен, пропускаем
            _logger.info("the order is already loaded %s", so)
            return False

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

        partner, address = get_partner(value_partner, value_address)

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

        # so_payment_type_id	ищем по полю website_ref в таблице so.payment.type
        # ??? website_id или biko_website_ref, ага website_ref в so.payment.type, но пока там пусто.
        payment_type = self.env["so.payment.type"].search(
            [("website_ref", "=", data_order.get("payment", None))], limit=1
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

        note = f"Номер: {order_id}. Доставка: {shipping} {data_order.get('address')} {partner.phone} {partner.email}"
        if data_order.get("comment"):
            note = data_order.get("comment") + " " + note

        so_values = {
            "partner_id": partner.id,
            "biko_contact_person_type": "person",
            "biko_contact_person_id": partner.id,
            "biko_recipient_id": partner.id,
            "biko_recipient_type": "person",
            "biko_website_ref": data_order.get("order_id"),
            "date_order": data_order.get("order_date"),
            "afterpayment_check": afterpayment_check,
            "note": note,
            "so_payment_type_id": payment_type,
            # "address": address,
            # "pricelist_value": pricelist_value,
            # "warehouse_value": warehouse_value,
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
        if products:
            product = products["product"]
            if isinstance(product, dict):
                get_so_line(so, product)
            else:
                for product_dict in product:
                    get_so_line(so, product_dict)

                # product_dict = products[ind]
                # if product_dict:

            #         so_count = self.load_data(dict_reply[ind].get("orders"))
            # for product_dict in products:
            #     if product_dict.get('product_id', False):

            # order_line = self.env["sale.order.line"].create(str_values)
            # order_line.product_id_change()

        return True
