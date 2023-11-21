import logging

from odoo import _, fields, models
from odoo.exceptions import UserError, ValidationError

from .utils import APIRequest

_logger = logging.getLogger(__name__)


class BaseSpreadSheetModel(models.AbstractModel):
    _name = "delivery_novaposhta.base_spreadsheet"

    """ Базовая абстрактная модель, от которой наследуются
        все остальные справочники"""

    name = fields.Char(string="Description")
    ref = fields.Char(string="Ref", index=True)
    active = fields.Boolean(default=True)

    """ Это инфа, которая должна быть отправлена в НП """
    data = {}
    """ Тут соответствие названия полей у нп и у нас в модели """
    create_data = {}

    def delete_all_records(self):
        self.search([]).unlink()

    def update_values(self):
        """Checks if changes were made to the spreadsheet in
        nova poshta servers and adds them to the records
        :return: None
        """
        try:
            key = (
                self.env["delivery_novaposhta.api_key"]
                .search([("active", "=", True)])[0]
                .key
            )
        except IndexError as error:
            raise ValidationError(_("There is no active API key!")) from error
        # records = {}
        records = self.env[self._name]
        data = self.data
        data["apiKey"] = key
        try:
            response = APIRequest.get_data(data)
        except ConnectionError as conn_error:
            raise UserError(_("Connection error")) from conn_error
        if isinstance(response, dict):
            _logger.error("the data was faulty, answer: {}".format(response))
        else:
            _logger.debug("data was ok, response: {}".format(response))
            self.env[self._name].search([("active", "=", True)]).write(
                {"active": False}
            )
            current_data = self.env[self._name].search_read(
                [("active", "=", False)], ["ref"]
            )
            current_data = [ref["ref"] for ref in current_data]
            _logger.debug("current refs: {}".format(current_data))
            for r in response:
                if r["Ref"] not in current_data:
                    _logger.debug("creating {}".format(r["Ref"]))
                    value = self.get_value(r)
                    self.env[self._name].create(value)
                    _logger.info("created {}".format(r["Ref"]))
                else:
                    self.env[self._name].search(
                        [("ref", "=", r["Ref"]), ("active", "=", False)]
                    ).write({"active": True})
        return records

    def get_value(self, r):
        res = {}
        try:
            res = {
                field_name: r[api_value]
                for field_name, api_value in self.create_data.items()
                if api_value in r
            }
            res["active"] = True
        except KeyError:
            _logger.warning("Error data: %s" % r)
        return res


class NovaPoshtaCargoTypes(models.Model):
    """
    Should be reloaded every month
    https://devcenter.novaposhta.ua/docs/services/55702570a0fe4f0cf4fc53ed/operations/55702571a0fe4f0b64838909

    "data": [
        {
          "Description": "Вантаж",
          "Ref": "Cargo"
        },
        {
          "Description": "Документи",
          "Ref": "Documents"
        },
        {
          "Description": "Шини-диски",
          "Ref": "TiresWheels"
        },
        {
          "Description": "Палети",
          "Ref": "Pallet"
        },
        {
          "Description": "Посилка",
          "Ref": "Parcel"
        }
    ],
    """

    _name = "delivery_novaposhta.cargo_types"
    _inherit = "delivery_novaposhta.base_spreadsheet"

    data = {
        "modelName": "Common",
        "calledMethod": "getCargoTypes",
        "methodProperties": {},
        "apiKey": "",
    }

    create_data = {
        "name": "Description",
        "ref": "Ref",
    }


class NovaPoshtaBackwardDeliveryCargoType(models.Model):
    """
    Should be reloaded every month
    https://devcenter.novaposhta.ua/docs/services/55702570a0fe4f0cf4fc53ed/operations/55702571a0fe4f0b64838907

    "data": [
        {
            "Description": "Документи",
            "Ref": "Documents"
        },
        {
            "Description": "Цінні папери",
            "Ref": "Money"
        },
        {
            "Description": "Піддони",
            "Ref": "Trays"
        },
        {
            "Description": "Інше",
            "Ref": "Other"
        }
    ],
    """

    _name = "delivery_novaposhta.backward_delivery_cargo_type"
    _inherit = "delivery_novaposhta.base_spreadsheet"
    data = {
        "modelName": "Common",
        "calledMethod": "getBackwardDeliveryCargoTypes",
        "methodProperties": {},
        "apiKey": "",
    }

    create_data = {
        "name": "Description",
        "ref": "Ref",
    }


class NovaPoshtaPalletsList(models.Model):
    """Бесполезный справочник, палеты нихрена не работают

    Should be reloaded every month
    https://devcenter.novaposhta.ua/docs/services/55702570a0fe4f0cf4fc53ed/operations/5824774ba0fe4f0e60694eb0

    "data": [
        {
            "Ref": "627b0c23-d110-11dd-8c0d-001d92f78697",
            "Description": "Палета від 1,5 м2 до 2 м2",
            "DescriptionRu": "Паллета свыше 1,5 м2",
            "Weight": "816.00"
        },
        {
            "Ref": "627b0c24-d110-11dd-8c0d-001d92f78697",
            "Description": "Палета від 1 м2 до 1,49 м2",
            "DescriptionRu": "Паллета от 1 м2 до 1,5 м2",
            "Weight": "612.00"
        },
        {
            "Ref": "627b0c25-d110-11dd-8c0d-001d92f78697",
            "Description": "Палета від 0,5 м2 до 0,99 м2",
            "DescriptionRu": "Паллета от 0,5 м2 до 1м2",
            "Weight": "408.00"
        },
        {
            "Ref": "627b0c26-d110-11dd-8c0d-001d92f78697",
            "Description": "Палета до 0,49 м2",
            "DescriptionRu": "Паллета до 0,49 м2",
            "Weight": "204.00"
        }
    ],
    """

    _name = "delivery_novaposhta.pallets_list"
    _inherit = "delivery_novaposhta.base_spreadsheet"
    weight = fields.Float(string="Weight")

    data = {
        "modelName": "Common",
        "calledMethod": "getPalletsList",
        "apiKey": "",
    }

    create_data = {
        "name": "Description",
        "ref": "Ref",
        "weight": "Weight",
    }


class NovaPoshtaTypesOfPayers(models.Model):
    """
    Should be reloaded every month
    https://devcenter.novaposhta.ua/docs/services/55702570a0fe4f0cf4fc53ed/operations/55702571a0fe4f0b64838913

    "data": [
        {
            "Description": "Відправник",
            "Ref": "Sender"
        },
        {
            "Description": "Одержувач",
            "Ref": "Recipient"
        },
        {
            "Description": "Третя особа",
            "Ref": "ThirdPerson"
        }
    ],
    """

    _name = "delivery_novaposhta.types_of_payers"
    _inherit = "delivery_novaposhta.base_spreadsheet"
    data = {
        "modelName": "Common",
        "calledMethod": "getTypesOfPayers",
        "methodProperties": {},
        "apiKey": "",
    }

    create_data = {
        "name": "Description",
        "ref": "Ref",
    }


class NovaPoshtaTypesOfPayersForRedelivery(models.Model):
    """
    Should be reloaded every month
    https://devcenter.novaposhta.ua/docs/services/55702570a0fe4f0cf4fc53ed/operations/55702571a0fe4f0b64838914

    "data": [
        {
            "Description": "Відправник",
            "Ref": "Sender"
        },
        {
            "Description": "Одержувач",
            "Ref": "Recipient"
        }
    ],
    """

    _name = "delivery_novaposhta.types_of_payers_for_redelivery"
    _inherit = "delivery_novaposhta.base_spreadsheet"
    data = {
        "modelName": "Common",
        "calledMethod": "getTypesOfPayersForRedelivery",
        "methodProperties": {},
        "apiKey": "",
    }

    create_data = {
        "name": "Description",
        "ref": "Ref",
    }


class NovaPoshtaPackList(models.Model):
    """
    Should be reloaded every month
    https://devcenter.novaposhta.ua/docs/services/55702570a0fe4f0cf4fc53ed/operations/582b1069a0fe4f0298618f06

    "data": [
        {
            "Ref": "c5d49e74-4ea1-11e2-889f-001631fa0467",
            "Description": "Пакування в стрейч плівку (0.1-2 кг)",
            "DescriptionRu": "Упаковка в стрейч пленку (0.1-2 кг)",
            "Length": "200.0",
            "Width": "200.0",
            "Height": "200.0",
            "TypeOfPacking": ""
        },
        {
            "Ref": "2886c0a1-5d76-11e3-b441-0050568002cf",
            "Description": "Пакування пінопластом в коробку (3кг)",
            "DescriptionRu": "Упаковка пенопластом в коробку  (3кг)",
            "Length": "230.0",
            "Width": "230.0",
            "Height": "210.0",
            "TypeOfPacking": ""
        },
        {
            "Ref": "f6f72e4d-5daf-11e3-b441-0050568002cf",
            "Description": "Коробка (3 кг) ",
            "DescriptionRu": "Коробка (3 кг) ",
            "Length": "230.0",
            "Width": "230.0",
            "Height": "210.0",
            "TypeOfPacking": ""
        },
        {
            "Ref": "10faca52-fc54-11df-ad22-0024e83b596e",
            "Description": "Коробка (5 кг)",
            "DescriptionRu": "Коробка (5 кг)",
            "Length": "390.0",
            "Width": "230.0",
            "Height": "210.0",
            "TypeOfPacking": ""
        },
        {
            "Ref": "af028e93-6407-11e0-bc54-0026b97ed48a",
            "Description": "Пакування пінопластом в коробку (5 кг)",
            "DescriptionRu": "Упаковка пенопластом в коробку (5 кг) ",
            "Length": "390.0",
            "Width": "230.0",
            "Height": "210.0",
            "TypeOfPacking": ""
        },
        {
            "Ref": "63e53f67-5098-11e0-ad70-fac2898a22b9",
            "Description": "Коробка (10 кг)",
            "DescriptionRu": "Коробка (10 кг)",
            "Length": "390.0",
            "Width": "340.0",
            "Height": "280.0",
            "TypeOfPacking": ""
        },
        {
            "Ref": "af028e91-6407-11e0-bc54-0026b97ed48a",
            "Description": "Пакування пінопластом в коробку (10 кг)",
            "DescriptionRu": "Упаковка пенопластом в коробку  (10 кг)",
            "Length": "390.0",
            "Width": "340.0",
            "Height": "280.0",
            "TypeOfPacking": ""
        },
        {
            "Ref": "ab0cd73d-da19-11e1-aa18-d4ae527baec9",
            "Description": "Коробка (15 кг)",
            "DescriptionRu": "Коробка (15 кг)",
            "Length": "590.0",
            "Width": "340.0",
            "Height": "280.0",
            "TypeOfPacking": ""
        },
        {
            "Ref": "ab0cd740-da19-11e1-aa18-d4ae527baec9",
            "Description": "Пакування пінопластом в коробку (15 кг)",
            "DescriptionRu": "Упаковка пенопластом в коробку  (15 кг)",
            "Length": "590.0",
            "Width": "340.0",
            "Height": "280.0",
            "TypeOfPacking": ""
        },
        {
            "Ref": "2886c0a2-5d76-11e3-b441-0050568002cf",
            "Description": "Пакування пінопластом в коробку (20 кг)",
            "DescriptionRu": "Упаковка пенопластом в коробку  (20 кг)",
            "Length": "460.0",
            "Width": "420.0",
            "Height": "390.0",
            "TypeOfPacking": ""
        },
        {
            "Ref": "f6f72e4e-5daf-11e3-b441-0050568002cf",
            "Description": "Коробка (20 кг)",
            "DescriptionRu": "Коробка (20 кг)",
            "Length": "460.0",
            "Width": "420.0",
            "Height": "390.0",
            "TypeOfPacking": ""
        },
        {
            "Ref": "2886c0a3-5d76-11e3-b441-0050568002cf",
            "Description": "Пакування пінопластом в коробку (30 кг)",
            "DescriptionRu": "Упаковка пенопластом в коробку  (30 кг)",
            "Length": "680.0",
            "Width": "380.0",
            "Height": "410.0",
            "TypeOfPacking": ""
        },
        {
            "Ref": "f6f72e4f-5daf-11e3-b441-0050568002cf",
            "Description": "Коробка (30 кг)",
            "DescriptionRu": "Коробка (30 кг)",
            "Length": "680.0",
            "Width": "380.0",
            "Height": "410.0",
            "TypeOfPacking": ""
        },
        {
            "Ref": "c5d49e75-4ea1-11e2-889f-001631fa0467",
            "Description": "Пакування в стрейч плівку (2-30 кг)",
            "DescriptionRu": "Упаковка в стрейч пленку (2-30 кг)",
            "Length": "500.0",
            "Width": "500.0",
            "Height": "480.0",
            "TypeOfPacking": ""
        },
        {
            "Ref": "ab0cd73e-da19-11e1-aa18-d4ae527baec9",
            "Description": "Коробка (40 кг)",
            "DescriptionRu": "Коробка (40 кг)",
            "Length": "680.0",
            "Width": "530.0",
            "Height": "440.0",
            "TypeOfPacking": ""
        },
        {
            "Ref": "ab0cd741-da19-11e1-aa18-d4ae527baec9",
            "Description": "Пакування пінопластом в коробку (40 кг)",
            "DescriptionRu": "Упаковка пенопластом в коробку  (40 кг)",
            "Length": "680.0",
            "Width": "530.0",
            "Height": "440.0",
            "TypeOfPacking": ""
        },
        {
            "Ref": "c5d49e76-4ea1-11e2-889f-001631fa0467",
            "Description": "Пакування в стрейч плівку (30-100 кг)",
            "DescriptionRu": "Упаковка в стрейч пленку (30-100 кг)",
            "Length": "750.0",
            "Width": "750.0",
            "Height": "710.0",
            "TypeOfPacking": ""
        },
        {
            "Ref": "c7e2e1a1-503f-11e2-912b-d4ae52ab9fab",
            "Description": "Пакування в стрейч плівку (більше 100 кг)",
            "DescriptionRu": "Упаковка в стрейч пленку (больше 100 кг)",
            "Length": "750.0",
            "Width": "750.0",
            "Height": "720.0",
            "TypeOfPacking": ""
        }
    ],
    """

    _name = "delivery_novaposhta.pack_list"
    _inherit = "delivery_novaposhta.base_spreadsheet"
    length = fields.Float()  # pylint: disable=attribute-deprecated
    width = fields.Float()
    height = fields.Float()
    TypeOfPacking = fields.Char()

    data = {
        "modelName": "Common",
        "calledMethod": "getPackList",
        "methodProperties": {
            "Length": "",
            "Width": "",
            "Height": "",
            "TypeOfPacking": "",
        },
        "apikey": "",
    }

    create_data = {
        "name": "Description",
        "ref": "Ref",
        "length": "Length",
        "width": "Width",
        "height": "Height",
        "TypeOfPacking": "TypeOfPacking",
    }


class NovaPoshtaTiresWheelsList(models.Model):
    """
    Should be reloaded every month
    https://devcenter.novaposhta.ua/docs/services/55702570a0fe4f0cf4fc53ed/operations/55702571a0fe4f0b64838910

    "data": [
        {
            "Ref": "20f7b625-9add-11e3-b441-0050568002cf",
            "Description": "Шина вантажна R 22,5",
            "DescriptionRu": "Шина грузовая R 22,5",
            "Weight": "94.00",
            "DescriptionType": "Tires"
        },
        {
            "Ref": "20f7b626-9add-11e3-b441-0050568002cf",
            "Description": "Шина вантажна R 17,5 ",
            "DescriptionRu": "Шина грузовая R 17,5",
            "Weight": "35.00",
            "DescriptionType": "Tires"
        },
        {
            "Ref": "20f7b627-9add-11e3-b441-0050568002cf",
            "Description": "Шина вантажна R 19,5",
            "DescriptionRu": "Шина грузовая R 19,5",
            "Weight": "61.00",
            "DescriptionType": "Tires"
        },
        {
            "Ref": "20f7b628-9add-11e3-b441-0050568002cf",
            "Description": "Шина вантажна R 20",
            "DescriptionRu": "Шина грузовая R 20",
            "Weight": "105.00",
            "DescriptionType": "Tires"
        },
        {
            "Ref": "d7c456c5-aa8b-11e3-9fa0-0050568002cf",
            "Description": "Шина легкова R 13-14",
            "DescriptionRu": "Шина легковая R 13-14",
            "Weight": "14.90",
            "DescriptionType": "Tires"
        },
        {
            "Ref": "d7c456c6-aa8b-11e3-9fa0-0050568002cf",
            "Description": "Шина легкова R 15-17",
            "DescriptionRu": "Шина легковая R 15-17",
            "Weight": "23.09",
            "DescriptionType": "Tires"
        },
        {
            "Ref": "d7c456c7-aa8b-11e3-9fa0-0050568002cf",
            "Description": "Шина легкова R 18-19",
            "DescriptionRu": "Шина легковая R 18-19",
            "Weight": "29.48",
            "DescriptionType": "Tires"
        },
        {
            "Ref": "d7c456c8-aa8b-11e3-9fa0-0050568002cf",
            "Description": "Шина легкова R 20-21",
            "DescriptionRu": "Шина легковая R 20-21",
            "Weight": "34.77",
            "DescriptionType": "Tires"
        },
        {
            "Ref": "d7c456c9-aa8b-11e3-9fa0-0050568002cf",
            "Description": "Шина легкова R 23",
            "DescriptionRu": "Шина легковая R 23",
            "Weight": "43.32",
            "DescriptionType": "Tires"
        },
        {
            "Ref": "d7c456ca-aa8b-11e3-9fa0-0050568002cf",
            "Description": "Диск вантажний R 17,5 ",
            "DescriptionRu": "Диск грузовой R 17,5",
            "Weight": "28.00",
            "DescriptionType": "Wheels"
        },
        {
            "Ref": "d7c456cb-aa8b-11e3-9fa0-0050568002cf",
            "Description": "Диск вантажний R 19,5",
            "DescriptionRu": "Диск грузовой R 19,5",
            "Weight": "45.00",
            "DescriptionType": "Wheels"
        },
        {
            "Ref": "d7c456cc-aa8b-11e3-9fa0-0050568002cf",
            "Description": "Диск вантажний R 20",
            "DescriptionRu": "Диск грузовой R 20",
            "Weight": "80.00",
            "DescriptionType": "Wheels"
        },
        {
            "Ref": "d7c456cd-aa8b-11e3-9fa0-0050568002cf",
            "Description": "Диск вантажний R 22,5",
            "DescriptionRu": "Диск грузовой R 22,5",
            "Weight": "70.00",
            "DescriptionType": "Wheels"
        },
        {
            "Ref": "d7c456cf-aa8b-11e3-9fa0-0050568002cf",
            "Description": "Диск легковий R 13-14",
            "DescriptionRu": "Диск легковой R 13-14",
            "Weight": "8.75",
            "DescriptionType": "Wheels"
        },
        {
            "Ref": "d7c456d0-aa8b-11e3-9fa0-0050568002cf",
            "Description": "Диск легковий R 15-17",
            "DescriptionRu": "Диск легковой R 15-17",
            "Weight": "15.42",
            "DescriptionType": "Wheels"
        },
        {
            "Ref": "d7c456d1-aa8b-11e3-9fa0-0050568002cf",
            "Description": "Диск легковий R 18-19",
            "DescriptionRu": "Диск легковой R 18-19",
            "Weight": "23.75",
            "DescriptionType": "Wheels"
        },
        {
            "Ref": "d7c456d2-aa8b-11e3-9fa0-0050568002cf",
            "Description": "Диск легковий R 20-21",
            "DescriptionRu": "Диск легковой R 20-21",
            "Weight": "40.00",
            "DescriptionType": "Wheels"
        },
        {
            "Ref": "d7c456d3-aa8b-11e3-9fa0-0050568002cf",
            "Description": "Диск легковий R 23",
            "DescriptionRu": "Диск легковой R 23",
            "Weight": "52.50",
            "DescriptionType": "Wheels"
        }
    ],
    """

    _name = "delivery_novaposhta.tires_wheels_list"
    _inherit = "delivery_novaposhta.base_spreadsheet"
    weight = fields.Float()
    DescriptionType = fields.Char()

    data = {
        "apiKey": "",
        "modelName": "Common",
        "calledMethod": "getTiresWheelsList",
    }

    create_data = {
        "name": "Description",
        "ref": "Ref",
        "weight": "Weight",
        "DescriptionType": "DescriptionType",
    }


class NovaPoshtaCargoDescriptionList(models.Model):
    """
    Should be reloaded every month
    https://devcenter.novaposhta.ua/docs/services/55702570a0fe4f0cf4fc53ed/operations/55702571a0fe4f0b64838908

    "data":[
        {
            "Ref": "8f46973e-33e4-11e3-b441-0050568002cf",
            "Description": "DVD/HD- медіаплеєр"
        },
        {
            "Ref": "f297a497-3cb8-11dd-84e9-001a92567626",
            "Description": "абажур"
        },
        {
            "Ref": "f297a499-3cb8-11dd-84e9-001a92567626",
            "Description": "абразивна паста"
        },
    ],
    """

    _name = "delivery_novaposhta.cargo_descritpion_list"
    _inherit = "delivery_novaposhta.base_spreadsheet"
    data = {
        "apiKey": "",
        "modelName": "Common",
        "calledMethod": "getCargoDescriptionList",
        "methodProperties": {},
    }

    create_data = {
        "name": "Description",
        "ref": "Ref",
    }


class NovaPoshtaServiceTypes(models.Model):
    """
    Should be reloaded every month
    https://devcenter.novaposhta.ua/docs/services/55702570a0fe4f0cf4fc53ed/operations/55702571a0fe4f0b6483890e

    "data":[
        {
            "Description":"Двері-Двері",
            "Ref":"DoorsDoors"
        },
        {
            "Description":"Двері-Склад",
            "Ref":"DoorsWarehouse"
        },
        {
            "Description":"Склад-Склад",
            "Ref":"WarehouseWarehouse"
        },
        {
            "Description":"Склад-Двері",
            "Ref":"WarehouseDoors"
        }
    ],
    """

    _name = "delivery_novaposhta.service_types"
    _inherit = "delivery_novaposhta.base_spreadsheet"
    data = {
        "modelName": "Common",
        "calledMethod": "getServiceTypes",
        "apiKey": "",
        "methodProperties": {},
    }

    create_data = {
        "name": "Description",
        "ref": "Ref",
    }


class NovaPoshtaTypesOfCounterparties(models.Model):
    """
    Should be reloaded every month
    https://devcenter.novaposhta.ua/docs/services/55702570a0fe4f0cf4fc53ed/operations/55702571a0fe4f0b64838912

    "data": [
        {
            "Description": "Организация",
            "Ref": "Organization"
        },
        {
            "Description": "Частное лицо",
            "Ref": "PrivatePerson"
        }
    ],
    """

    _name = "delivery_novaposhta.types_of_counterparties"
    _inherit = "delivery_novaposhta.base_spreadsheet"
    data = {
        "modelName": "Common",
        "calledMethod": "getTypesOfCounterparties",
        "apiKey": "",
        "methodProperties": {},
    }

    create_data = {
        "name": "Description",
        "ref": "Ref",
    }


class NovaPoshtaNotification(models.Model):
    _name = "delivery_novaposhta.notification"

    text = fields.Char("Notification")
    notification = fields.Boolean()

    def send(self):
        notifications = (
            self.env["delivery.carrier"].sudo().search([("delivery_type", "=", "np")])
        )
        for r in notifications:
            r.notification = not r.notification
        return str(r.notification)


class NovaPoshtaPaymentForms(models.Model):
    """
    Should be reloaded every month
    https://devcenter.novaposhta.ua/docs/services/55702570a0fe4f0cf4fc53ed/operations/55702571a0fe4f0b6483890d

    "data":[
        {
            "Description":"Безналичный расчет",
            "Ref":"NonCash"
        },
        {
            "Description":"Наличный расчет",
            "Ref":"Cash"
        }
    ],
    """

    _name = "delivery_novaposhta.payments_forms"
    _inherit = "delivery_novaposhta.base_spreadsheet"
    data = {
        "modelName": "Common",
        "calledMethod": "getPaymentForms",
        "apiKey": "",
        "methodProperties": {},
    }

    create_data = {
        "name": "Description",
        "ref": "Ref",
    }


class NovaPoshtaOwnershipFormsList(models.Model):
    """
    Should be reloaded every month
    https://devcenter.novaposhta.ua/docs/services/55702570a0fe4f0cf4fc53ed/operations/55702571a0fe4f0b6483890b

    "data": [
        {
            "Ref": "7f0f3516-2519-11df-be9a-000c291af1b3",
            "Description": "ПК",
            "FullName": "Производственный кооператив"
        },
        {
            "Ref": "7f0f3515-2519-11df-be9a-000c291af1b3",
            "Description": "ГП",
            "FullName": "Государственное предприятие"
        },
        {
            "Ref": "7f0f3518-2519-11df-be9a-000c291af1b3",
            "Description": "КП",
            "FullName": "Коммунальное предприятие"
        },
        {
            "Ref": "10d78dad-2352-11e2-83ab-d4ae52ab9fab",
            "Description": "КО",
            "FullName": "Коммандитное общество"
        },
        {
            "Ref": "361b83db-886e-11e1-a146-0026b97ed48a",
            "Description": "ПАО",
            "FullName": "Публичное акционерное общество"
        },
        {
            "Ref": "9252696e-2202-11e4-acce-0050568002cf",
            "Description": "ПИИ",
            "FullName": "Предприятие с иностранными инвестициями"
        },
        {
            "Ref": "7f0f3519-2519-11df-be9a-000c291af1b3",
            "Description": "ЧП",
            "FullName": "Частное предприятие (не частный предприниматель)"
        },
        {
            "Ref": "b0b2c790-8920-11e1-8429-0026b97ed48a",
            "Description": "ЧАО",
            "FullName": "Акционерное общество (ПАО, ЧАО, ОАО, ЗАО)"
        },
        {
            "Ref": "7f0f3514-2519-11df-be9a-000c291af1b3",
            "Description": "ПО",
            "FullName": "Полное общество"
        },
        {
            "Ref": "7f0f351a-2519-11df-be9a-000c291af1b3",
            "Description": "СП",
            "FullName": "Совместное предприятие"
        },
        {
            "Ref": "7f0f351c-2519-11df-be9a-000c291af1b3",
            "Description": "ОДО",
            "FullName": ", Общество с дополнительной ответственностью"
        },
        {
            "Ref": "7f0f351d-2519-11df-be9a-000c291af1b3",
            "Description": "ООО",
            "FullName": ", Общество с ограниченной ответственностью"
        },
        {
            "Ref": "7f0f3517-2519-11df-be9a-000c291af1b3",
            "Description": "ФХ",
            "FullName": "Фермерское хозяйство"
        },
        {
            "Ref": "7f0f351e-2519-11df-be9a-000c291af1b3",
            "Description": "ФЛП (СПД)",
            "FullName": "Физ. Лицо-предприниматель (только частный предприниматель)"
        }
    ],
    """

    _name = "delivery_novaposhta.ownership_forms_list"
    _inherit = "delivery_novaposhta.base_spreadsheet"
    full_name = fields.Char()
    data = {
        "modelName": "Common",
        "calledMethod": "getOwnershipFormsList",
        "apiKey": "",
        "methodProperties": {},
    }

    create_data = {
        "name": "Description",
        "ref": "Ref",
        "full_name": "FullName",
    }


class NovaPoshtaCitiesList(models.Model):
    """
    Should be reloaded every month
    https://devcenter.novaposhta.ua/docs/services/556d7ccaa0fe4f08e8f7ce43/operations/556d885da0fe4f08e8f7ce46

    "data": [
        {
            "Description": "Авангард",
            "DescriptionRu": "Авангард",
            "Ref": "YourRef",
            "Delivery1": "1",
            "Delivery2": "1",
            "Delivery3": "1",
            "Delivery4": "1",
            "Delivery5": "1",
            "Delivery6": "0",
            "Delivery7": "0",
            "Area": "71508136-9b87-11de-822f-000c2965ae0e",
            "SettlementType": "563ced11-f210-11e3-8c4a-0050568002cf",
            "IsBranch": "0",
            "PreventEntryNewStreetsUser": null,
            "Conglomerates": null,
            "CityID": "1042",
            "SettlementTypeDescriptionRu": "село городского типа",
            "SettlementTypeDescription": "селище міського типу"
        },
    """

    _name = "delivery_novaposhta.cities_list"
    _inherit = "delivery_novaposhta.base_spreadsheet"
    streets_ids = fields.One2many(
        "delivery_novaposhta.streets_list", "city_id", "Streets"
    )
    warehouse_ids = fields.One2many(
        "delivery_novaposhta.warehouse", "city_id", "Warehouses"
    )
    name_ru = fields.Char("Name ru")
    type_ru = fields.Char("Type ru")
    type = fields.Char("Type")
    data = {
        "modelName": "Address",
        "calledMethod": "getCities",
        "methodProperties": {},
        "apiKey": "",
    }
    create_data = {
        "name": "Description",
        "name_ru": "DescriptionRu",
        "type": "SettlementTypeDescription",
        "type_ru": "SettlementTypeDescriptionRu",
        "ref": "Ref",
    }

    def get_website_sale_warehouse(self, mode):
        return self.warehouse_ids

    def action_update_warhouses(self):
        for city in self:
            self.env["delivery_novaposhta.warehouse"].update_values(city=city)


class NovaPoshtaStreetLists(models.Model):
    """
       Should be reloaded every month
       https://devcenter.novaposhta.ua/docs/services/556d7ccaa0fe4f08e8f7ce43/operations/556d8db0a0fe4f08e8f7ce47

    "data": [
        {
            "Description": "Академічна",
            "Ref": "b5e79222-2d34-11e4-acce-0050568002cf",
            "StreetsTypeRef": "Street",
            "StreetsType": "вул."
        },
        {
            "Description": "Будівельників",
            "Ref": "7b4f37cc-6e34-11e4-acce-0050568002cf",
            "StreetsTypeRef": "Highway",
            "StreetsType": "шосе"
        },
        {
            "Description": "Вінницька",
            "Ref": "9be2d800-0833-11e4-acce-0050568002cf",
            "StreetsTypeRef": "Street",
            "StreetsType": "вул."
        },
        {
            "Description": "Гагаріна",
            "Ref": "a76c21a5-0c01-11e4-acce-0050568002cf",
            "StreetsTypeRef": "Street",
            "StreetsType": "вул."
        },
        {
            "Description": "Дачна",
            "Ref": "2e3091c2-6195-11e4-acce-0050568002cf",
            "StreetsTypeRef": "Street",
            "StreetsType": "вул."
        },
        {
            "Description": "Житня",
            "Ref": "e54f35ea-c18e-11e4-a77a-005056887b8d",
            "StreetsTypeRef": "Street",
            "StreetsType": "вул."
        },
        {
            "Description": "Квітнева ",
            "Ref": "1e529c5c-6fba-11e4-acce-0050568002cf",
            "StreetsTypeRef": "Street",
            "StreetsType": "вул."
        },
        {
            "Description": "Малиновського ",
            "Ref": "487de665-cbf0-11e4-a77a-005056887b8d",
            "StreetsTypeRef": "Street",
            "StreetsType": "вул."
        },
        {
            "Description": "Мічуріна",
            "Ref": "a76c21a3-0c01-11e4-acce-0050568002cf",
            "StreetsTypeRef": "Street",
            "StreetsType": "вул."
        },
        {
            "Description": "Молодіжна",
            "Ref": "a76c21a6-0c01-11e4-acce-0050568002cf",
            "StreetsTypeRef": "Street",
            "StreetsType": "вул."
        },
        {
            "Description": "Мудрого Ярослава",
            "Ref": "a76c21a7-0c01-11e4-acce-0050568002cf",
            "StreetsTypeRef": "Street",
            "StreetsType": "вул."
        },
        {
            "Description": "Наукова",
            "Ref": "b77f7846-8756-11e4-acce-0050568002cf",
            "StreetsTypeRef": "Street",
            "StreetsType": "вул."
        },
        {
            "Description": "Прибережна ",
            "Ref": "b94e8a22-85bf-11e4-acce-0050568002cf",
            "StreetsTypeRef": "Street",
            "StreetsType": "вул."
        },
        {
            "Description": "Садова ",
            "Ref": "83c507e1-bcee-11e4-a77a-005056887b8d",
            "StreetsTypeRef": "Street",
            "StreetsType": "вул."
        },
        {
            "Description": "Тимірязєва ",
            "Ref": "02cb4007-6fde-11e4-acce-0050568002cf",
            "StreetsTypeRef": "Street",
            "StreetsType": "вул."
        },
        {
            "Description": "Яблунева",
            "Ref": "0e4a2d7e-372d-11e4-acce-0050568002cf",
            "StreetsTypeRef": "Street",
            "StreetsType": "вул."
        },
    """

    _name = "delivery_novaposhta.streets_list"
    _inherit = "delivery_novaposhta.base_spreadsheet"
    city_id = fields.Many2one("delivery_novaposhta.cities_list", "City")
    city_name = fields.Char()
    city_ref = fields.Char()
    street_type = fields.Char()
    street_type_ref = fields.Char()
    data = {
        "modelName": "Address",
        "calledMethod": "getStreet",
        "methodProperties": {"CityRef": ""},
        "apiKey": "",
    }

    create_data = {
        "name": "Description",
        "ref": "Ref",
        "street_type_ref": "StreetsTypeRef",
        "street_type": "StreetsType",
    }

    def create_street(self, np_data, current_city):
        _logger.debug("data was ok, response: {}".format(np_data))
        current_streets = self.env["delivery_novaposhta.streets_list"].search_read(
            [], ["ref"]
        )
        # array of refs
        current_streets = [ref["ref"] for ref in current_streets]
        _logger.debug("current refs: {}".format(current_streets))
        city_street_list = []
        if current_city.streets_ids:
            city_street_list += [street.ref for street in current_city.streets_ids]
        for record in np_data:
            if record["Ref"] not in current_streets:
                _logger.debug("creating {}".format(record["Ref"]))
                value = {
                    field_name: record[api_value]
                    for field_name, api_value in self.create_data.items()
                }
                value.update(
                    {
                        "city_ref": current_city.ref,
                        "city_name": current_city.name,
                        "city_id": current_city.id,
                    }
                )
                self.env["delivery_novaposhta.streets_list"].create(value)
                _logger.info("created {}".format(record["Ref"]))
            else:
                _logger.debug("No new records were found")
            if record["Ref"] not in city_street_list:
                street_id = self.search([("ref", "=", record["Ref"])], limit=1)
                self.env["delivery_novaposhta.cities_list"].write(
                    {"streets_ids": [(2, street_id)]}
                )

    def update_city(self, key, city):
        data = self.data
        data["apiKey"] = key
        data["methodProperties"]["CityRef"] = city.ref
        response = APIRequest.get_data(data)
        if isinstance(response, dict):
            _logger.error("the data was faulty, answer: {}".format(response))
        else:
            self.create_street(response, city)

    def update_values(self):
        """
        Checks if changes were made to the spreadsheet in
        nova poshta servers and adds them to the records
        :return: None
        """
        try:
            key = (
                self.env["delivery_novaposhta.api_key"]
                .search([("active", "=", True)])[0]
                .key
            )
        except IndexError as idx_error:
            raise ValidationError(_("There is no active API key!")) from idx_error

        city_list_ids = self.env["delivery_novaposhta.cities_list"].search([])
        for city in city_list_ids:
            self.with_delay().update_city(key, city)


class NovaPoshtaAreasLists(models.Model):
    _name = "delivery_novaposhta.areas_list"
    _inherit = "delivery_novaposhta.base_spreadsheet"

    areas_center = fields.Char()

    data = {
        "modelName": "Address",
        "calledMethod": "getAreas",
        "methodProperties": {},
        "apiKey": "",
    }

    create_data = {
        "name": "Description",
        "ref": "Ref",
        "areas_center": "AreasCenter",
    }


class SyncStreetsList(models.TransientModel):
    _name = "delivery_novaposhta.sync_street_list"

    city_id = fields.Many2one("delivery_novaposhta.cities_list")

    def synchronize(self):
        try:
            key = self.env["delivery_novaposhta.api_key"].search(
                [("active", "=", True)], limit=1
            )
        except IndexError as idx_error:
            raise ValidationError(_("There is no active API key!")) from idx_error

        # Delete the current street catalog for the selected city from the database
        # Create a new catalog. This is faster than checking every new record against an existing one.
        self.env.cr.execute(
            """DELETE FROM delivery_novaposhta_streets_list
                               WHERE city_id=%s""",
            (self.city_id.id,),
        )

        page = 1
        flag = True

        while flag:
            data = {
                "apiKey": key.key,
                "modelName": "Address",
                "calledMethod": "getStreet",
                "methodProperties": {
                    "CityRef": self.city_id.ref,
                    "Page": str(page),
                },
            }

            try:
                response = APIRequest.get_data(data)
            except ConnectionError as conn_error:
                raise ValidationError(_("Connection Error")) from conn_error

            if response:
                for street in response:
                    self.env["delivery_novaposhta.streets_list"].create(
                        {
                            "city_id": self.city_id.id,
                            "city_name": self.city_id.name,
                            "city_ref": self.city_id.ref,
                            "name": street.get("Description"),
                            "ref": street.get("Ref"),
                            "street_type": street.get("StreetsType"),
                            "street_type_ref": street.get("StreetsTypeRef"),
                        }
                    )
                page += 1
            else:
                flag = False
