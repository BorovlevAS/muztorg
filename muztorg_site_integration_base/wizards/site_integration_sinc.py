import json
import logging
import tempfile

import requests

from odoo import fields, models

from ..muztorg_api.api import MTApi

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
        headers = {
            # "Content-Type": "application/json; charset=cp1251",
            "Content-Type": "text/xml",
            # "token": self.autoclient_token,
            # "id": self.autoclient_id,
            # "User-Agent": "клиентское приложение".encode(),
        }
        url = "https://muztorg.ua/index.php?route=dwebexporter/exporting&id=orders"
        url = "https://muztorg.ua/index.php?"
        API = MTApi(url, "")  # self._get_rest_endpoint(website, **kwargs)
        # for message in data:
        #     API.send_data(json.dumps(message))
        message = ""
        API.send_data(json.dumps(message))
        response = requests.get(
            url,
            params={"route": "dwebexporter/exporting", "id": "orders"},
            headers=headers,
            timeout=10.0,
        )

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
