import json
import logging
import tempfile

# import XML2Dict
from encoder import XML2Dict

from odoo import fields, models

from ..muztorg_api.api import MTApi

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
        # headers = {
        #     # "Content-Type": "application/json; charset=cp1251",
        #     "Content-Type": "text/xml",
        #     # "token": self.autoclient_token,
        #     # "id": self.autoclient_id,
        #     # "User-Agent": "клиентское приложение".encode(),
        # }
        url = "https://muztorg.ua/index.php?route=dwebexporter/exporting&id=orders"
        # url = "https://muztorg.ua/index.php?"
        API = MTApi(url, "")  # self._get_rest_endpoint(website, **kwargs)
        # for message in data:
        #     API.send_data(json.dumps(message))
        # message = ""
        response = API.import_data()

        if response:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".xml") as temp_file:
                temp_file.write(response.content, encoding="utf-8")
                temp_file_path = temp_file.name

            # canonicalize(xml_data, out=out_file), encoding='utf-8'
            #
            # tree = ET.parse(temp_file_path)
            # root = tree.getroot()
            # for child in root:
            #     print(child.tag, child.attrib, child.text)
            #     if child.find('remind_orders'):
            #         print(child.tag, child.attrib, child.text)
            #     if child.find('orders'):
            #         print(child.tag, child.attrib, child.text)
            # root = ET.fromstring(response.content)
            # ET.fromstring(base64.b64decode(response.content))
            # xmldata = ET.tostring(root, encoding='windows-1251', method='xml')
            # ET.tostring(
            #      root,
            #      encoding='us-ascii',
            #      method='xml',
            #     #  *,
            #      xml_declaration=None,
            #      default_namespace=None,
            #      short_empty_elements=True)
            #
            # with open(temp_file_path, encoding='utf-8') as temp_file:
            # str_xml= ET.canonicalize(from_file = temp_file.name)
            # str_json = json.dumps(xml2dict.parse(str_xml), indent=4)
            # print(str_json)
            #
            # print(json.loads(str_json))
            # str_xml= ET.canonicalize(from_file = temp_file.name)
            obj = XML2Dict(coding="utf-8")
            obj.parse(response.content)

            # dict = xml2dict.parse(str_xml)
            # if len(dict) != 0:
            #     for feed in dict:
            #         print(feed)

        if response.status_code == 200:
            # Сохранение файла во временном месте
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file.write(response.content)
                temp_file_path = temp_file.name

            # Распарсивание файла
            with open(temp_file_path) as file:
                json.load(file)

            # Обработка данных и создание/обновление записей в Odoo
            # Например:
            # for order in data.get('orders', []):
            # Создание или обновление заказов в Odoo
            # order - это словарь с данными заказа
            # Ваш код для создания/обновления записей в Odoo

            # Удаление временного файла после использования
            # import os
            # os.unlink(temp_file_path)
            return True
        else:
            # print("Failed to download file")
            _logger.exception("""Failed to download file""")
            return False
