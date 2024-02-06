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
        for order in data.get("order"):
            self.load_order(order)

    def get_partner(
        self, phone_code, telephone, email, lastname, firstname, patronymic
    ):
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

        def search_partner(phone, email, lastname, firstname):
            # ICPSudo = request.env["ir.config_parameter"].sudo()
            # company_id = ICPSudo.get_param(
            #     "kapitanova_website_api.company_kapitanova", ""
            # )

            # company = (
            #     request.env["res.company"].sudo().search([("id", "=", company_id)])
            # )

            # if not company:
            #     _logger.error("-----------------client_push Company was not found")
            #     return False

            # Partner = self.env["res.partner"].with_company(company.id).sudo()
            Partner = self.env["res.partner"].sudo()

            partner_domain = [
                "|",
                ("mobile", "=", phone),
                ("biko_1c_phone", "=", phone),
            ]
            partner = Partner.search(partner_domain, limit=1)

            if partner:
                return partner

            partner_domain = [
                ("email", "=", email),
            ]
            partner = Partner.search(partner_domain, limit=1)

            if partner:
                return partner

            data = {
                "lastname": lastname,
                "firstname": firstname,
                "phone": phone,
                "email": email,
                "country_id": self.env.ref("base.ua").id,
                "type": "contact",
                "lang": self.env.lang,
            }
            _logger.info("create a partner %s", lastname)
            return Partner.create(data)

        _logger.info("-----------------search for a partner %s", lastname)
        phone = format_phone(phone_code + telephone)

        if patronymic:
            firstname = firstname + " " + patronymic

        # errors = []

        # if not phone:
        #     errors.append("phone not specified")

        # if not lastname:
        #     errors.append("name not specified")

        # if errors:
        #     result = {"result": False, "errors": errors}
        #     return result

        partner = search_partner(phone, email, lastname, firstname)

        if not partner:
            # result = {"result": False, "errors": ["Error creating partner"]}
            return False

        # result = {"result": True, "partner_id": partner.id}
        return partner

    def get_address(self, partner, city, city_ref, address, warehouse_ref, shipping):
        def search_address(partner, city, warehouse, street=None):
            Partner = self.env["res.partner"].sudo()
            partner_domain = [
                ("parent_id", "=", partner.id),
                ("type", "=", "delivery"),
                ("np_delivery_address", "=", True),
                ("np_city", "=", city.id),
            ]
            if warehouse:
                partner_domain.append(("np_warehouse", "=", warehouse.id))
            elif street:
                partner_domain.append(("np_street", "=", street.id))

            partner = Partner.search(partner_domain, limit=1)

            if partner:
                return partner

        _logger.info("search addressr %s", address)

        if shipping != "NOVA POSHTA":
            return False
        CitiesList = self.env["delivery_novaposhta.cities_list"].sudo()
        city_ref = CitiesList.search([("ref", "=", city_ref)], limit=1)
        if not city_ref:
            _logger.info("city not found %s", city)
            return False
        if warehouse_ref:
            WarehouseNP = self.env["delivery_novaposhta.warehouse"].sudo()
            warehouse = WarehouseNP.search([("ref", "=", warehouse_ref)], limit=1)
        street = self.env["delivery_novaposhta.streets_list"]
        if address and not warehouse_ref:
            streer_str = address.split(",")[0]
            StreetNP = self.env["delivery_novaposhta.streets_list"].sudo()
            street = StreetNP.search(
                [("city_id", "=", city_ref.id), ("name", "=", streer_str)], limit=1
            )

        partner_address = search_address(partner, city_ref, warehouse, street)

        if not partner_address:
            # result = {"result": False, "errors": ["Error creating partner"]}
            return False

        # result = {"result": True, "partner_id": partner.id}
        return partner_address

    def load_order(self, data_order):
        if data_order.get("order_id"):
            so = self.env["sale.order"].search(
                [("biko_website_ref", "=", data_order.get("order_id"))]
            )
            if so:
                #  уже загружен, пропускаем
                _logger.info("the order is already loaded %s", so)
                return False

            shipping = data_order.get("shipping", None)
            order_id = data_order.get("order_id", None)

            partner = self.get_partner(
                data_order.get("phone_code", None),
                data_order.get("telephone", None),
                data_order.get("email", None),
                data_order.get("lastname", None),
                data_order.get("firstname", None),
                data_order.get("patronymic", None),
            )

            address = self.get_address(
                partner,
                data_order.get("city", None),
                data_order.get("city_ref", None),
                data_order.get("address", None),
                data_order.get("warehouse", None),
                shipping,
            )

            pricelist_value = (
                self.env["site.integration.setting.line"]
                .search(
                    [
                        ("settings_id", "=", self.settings_id.id),
                        ("setting_id.id_seting", "=", "id_prajs"),
                    ]
                )
                .value_many2one
            )

            # so_payment_type_id	ищем по полю website_ref в таблице so.payment.type
            # ??? website_id или biko_website_ref, ага website_ref в so.payment.type, но пока там пусто.
            # payment_types = self.env["so.payment.type"].search(
            #     [("fiscal_receipt_req", "in", ["yes", "after_receive"])]
            # )

            # склад
            # warehouse_id	Склад отгрузки определяем так: если shipping = 'NOVA POSHTA', то это всегда склад головний, (!!!! а где он прячется?)
            # если SamovyvozMTPodol, то это склад подол
            warehouse_value = (
                self.env["site.integration.setting.line"]
                .search(
                    [
                        ("settings_id", "=", self.settings_id.id),
                        ("setting_id.id_seting", "=", "id_sklad_podil"),
                    ]
                )
                .value_many2one
            )
            # carrier_id	Способ доставки - если shipping = 'NOVA POSHTA', то это Новая почта, если SamovyvozMTPodol - самовывоз

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
            data_order.get("address", None)

            note = f"Номер: {order_id}. Доставка: {shipping} {data_order.get('address')} {partner.phone} {partner.email}"

            so_values = {
                "partner_id": partner.id,
                "biko_contact_person_type": "person",
                "biko_contact_person_id": partner.id,
                "biko_recipient_id": partner.id,
                "biko_website_ref": data_order.get("order_id"),
                "date_order": data_order.get("order_date"),
                "afterpayment_check": afterpayment_check,
                "note": note,
                # "address": address,
                # "pricelist_value": pricelist_value,
                # "warehouse_value": warehouse_value,
            }
            if carrier_value:
                so_values["carrier_id"] = carrier_value.id
            if pricelist_value:
                so_values["carrier_id"] = pricelist_value.id

            if address:
                so_values["carrier_id"] = address.id
            if warehouse_value:
                so_values["carrier_id"] = warehouse_value.id
            #    so_values.
            # "partner_shipping_id":
            # 'pricelist_id': ,

            return so_values


#      new_lines = self.env['sale.order.line']
# for line in self.opportunity_id.lead_product_ids:

#     data = self._prepare_sale_order_lines_from_opportunity(line)
#     new_line = new_lines.new(data)
#     new_lines += new_line

# self.order_line += new_lines

#      def get_values_convert2saleorder(self):
#     return {
#         "name": self.name,
#         "partner_id": self.partner_id.id,
#         "team_id": self.team_id.id,
#         "campaign_id": self.campaign_id.id,
#         "source_id": self.source_id.id,
#         "medium_id": self.medium_id.id,
#         "tag_ids": [(6, 0, self.tag_ids.ids)],
#     }

# def action_button_convert2saleorder(self):
#     """Convert a phonecall into SO and redirect to the SO view."""
#     self.ensure_one()
#     so = self.env["sale.order"]
#     so_id = so.create(self.get_values_convert2saleorder())

#  order_line = self.env["sale.order.line"].create(
#                 {
#                     "order_id": self.res_id,
#                     "product_id": line.product_id.id,
#                     "product_uom_qty": line.qty,
#                     "price_unit": line.price_unit,
#                 }
#             )
#             order_line.product_id_change()

# values = {
#         'order_id': self.id,
#         'name': so_description,
#         'product_uom_qty': 1,
#         'product_uom': carrier.product_id.uom_id.id,
#         'product_id': carrier.product_id.id,
#         'tax_id': [(6, 0, taxes_ids)],
#         'is_delivery': True,
#     }

#  sample_sales_order = self.env['sale.order'].create({
#     'partner_id': partner.id
# })
# # take any existing product or create one
# product = self.env['product.product'].search([], limit=1)
# if len(product) == 0:
#     default_image_path = get_module_resource('product', 'static/img', 'product_product_13-image.png')
#     product = self.env['product.product'].create({
#         'name': _('Sample Product'),
#         'active': False,
#         'image_1920': base64.b64encode(open(default_image_path, 'rb').read())
#     })
#     product.product_tmpl_id.write({'active': False})
# self.env['sale.order.line'].create({
#     'name': _('Sample Order Line'),
#     'product_id': product.id,
#     'product_uom_qty': 10,
#     'price_unit': 123,
#     'order_id': sample_sales_order.id,
#     'company_id': sample_sales_order.company_id.id,
# })
