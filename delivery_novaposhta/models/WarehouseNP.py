import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from .utils import APIRequest

_logger = logging.getLogger(__name__)


class NovaPoshtaWarehouse(models.Model):
    """Справочник всех отделений НП.

    Ничего примечательного, выделен в отдельный файл по значимости.
    {
        "modelName": "AddressGeneral",
        "calledMethod": "getWarehouses",
        "methodProperties": {
            "CityName": "Киев",
            "Language": "ru"
        },
        "apiKey": "YourApiKey"
    }
    {
        "SiteKey": "105",
        "Description": "Відділення №1: вул. Пирогівський шлях, 135",
        "DescriptionRu": "Отделение №1: ул. Пироговский путь, 135",
        "ShortAddress": "Київ, Пирогівський шлях, 135",
        "ShortAddressRu": "Киев, Пироговский путь, 135",
        "Phone": "0-800-500-609",
        "TypeOfWarehouse": "9a68df70-0267-42a8-bb5c-37f427e36ee4",
        "Ref": "1ec09d88-e1c2-11e3-8c4a-0050568002cf",
        "Number": "1",
        "CityRef": "8d5a980d-391c-11dd-90d9-001a92567626",
        "CityDescription": "Київ",
        "CityDescriptionRu": "Киев",
        "Longitude": "30.542863000000000",
        "Latitude": "50.353444000000000",
        "PostFinance": "1",
        "BicycleParking": "1",
        "PaymentAccess": "0",
        "POSTerminal": "1",
        "InternationalShipping": "1",
        "TotalMaxWeightAllowed": 0,
        "PlaceMaxWeightAllowed": 0,
        "Reception": {
            "Monday": "08:00-23:00",
            "Tuesday": "08:00-23:00",
            "Wednesday": "08:00-23:00",
            "Thursday": "08:00-23:00",
            "Friday": "08:00-23:00",
            "Saturday": "08:00-23:00",
            "Sunday": "-"
        },
        "Delivery": {
            "Monday": "07:00-21:00",
            "Tuesday": "07:00-21:00",
            "Wednesday": "07:00-21:00",
            "Thursday": "07:00-21:00",
            "Friday": "07:00-21:00",
            "Saturday": "07:00-18:00",
            "Sunday": "-"
        },
        "Schedule": {
            "Monday": "07:00-23:00",
            "Tuesday": "07:00-23:00",
            "Wednesday": "07:00-23:00",
            "Thursday": "07:00-23:00",
            "Friday": "07:00-23:00",
            "Saturday": "07:00-23:00",
            "Sunday": "07:00-23:00"
        }
    }
    """

    _name = "delivery_novaposhta.warehouse"
    _inherit = "delivery_novaposhta.base_spreadsheet"
    address = fields.Char(string="Address")
    phone = fields.Char(string="Phone")
    number = fields.Integer(string="Number")
    cityref = fields.Char(string="City Ref")
    cityname = fields.Char(string="City Name")
    city_id = fields.Many2one("delivery_novaposhta.cities_list", "City")

    data = {
        "modelName": "AddressGeneral",
        "calledMethod": "getWarehouses",
        "methodProperties": {},
        "apiKey": "",
    }

    create_data = {
        "name": "Description",
        "ref": "Ref",
        "address": "ShortAddress",
        "phone": "Phone",
        "number": "Number",
        "cityref": "CityRef",
        "cityname": "CityDescription",
    }

    @api.model
    def update_values(self, **kwargs):
        """Checks if changes were made to the spreadsheet in
        nova poshta servers and adds them to the records
        :return: records
        """
        try:
            key = (
                self.env["delivery_novaposhta.api_key"]
                .search([("active", "=", True)])[0]
                .key
            )
        except IndexError as idx_error:
            raise ValidationError(_("There is no active API key!")) from idx_error

        city = kwargs.get("city", False)

        data = {
            "modelName": "AddressGeneral",
            "calledMethod": "getWarehouses",
            "methodProperties": {},
            "apiKey": "",
        }

        data["apiKey"] = key

        if city:
            data["methodProperties"].update(
                {
                    "CityRef": city.ref,
                }
            )

        try:
            response = APIRequest.get_data(data)
        except ConnectionError as conn_error:
            raise UserError(_("Connection error")) from conn_error

        if isinstance(response, dict):
            _logger.error("the data was faulty, answer: {}".format(response))
            return False
        else:
            _logger.info("++++NAVAPOSHTA got data. Len: {}".format(len(response)))
            index = 0
            for r in response:
                index += 1
                warehouse = self.search([("ref", "=", r["Ref"])])
                city = self.env["delivery_novaposhta.cities_list"].search(
                    [("ref", "=", r["CityRef"])]
                )
                if not warehouse:
                    _logger.info("++++NAVAPOSHTA creating {}".format(r["Ref"]))
                    value = self.get_value(r)
                    value.update({"city_id": city.id})

                    warehouse = self.env[self._name].create(value)

                    _logger.info(
                        "++++NAVAPOSHTA created {} - {} - {}".format(
                            warehouse.id, warehouse.name, warehouse.ref
                        )
                    )

                else:
                    if warehouse.city_id != city:
                        warehouse.city_id = city

            return True
