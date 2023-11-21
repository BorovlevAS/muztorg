import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from .utils import APIRequest

_logger = logging.getLogger(__name__)


class NovaPoshtaAPIKey(models.Model):
    # TODO: Add update button to update contact senders

    _name = "delivery_novaposhta.api_key"
    _rec_name = "key"

    key = fields.Char(required=True)
    active = fields.Boolean(default=True)
    senderref = fields.Char(readonly=True)
    sendertype = fields.Char(readonly=True)
    contacts = fields.One2many("delivery_novaposhta.sender_contact", "related_key")
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.user.company_id
    )

    @api.constrains("active")
    def _unique_active(self):
        """Проверяет, чтоб был только один активный ключ"""

        for record in self:
            if (
                record.active
                and len(
                    self.env["delivery_novaposhta.api_key"].search(
                        [
                            ("active", "=", True),
                            ("company_id", "=", record.company_id.id),
                        ]
                    )
                )
                > 1
            ):
                raise ValidationError(_("There can be only one active api key!"))

    @api.model
    def create(self, vals):
        """При добавлении ключа надо сразу грузить контрагента и
        контактное лицо отправителя, так как оно привязано к ключу апи"""

        _logger.debug("Get active api key")
        key = vals["key"]
        _logger.debug("API key: {}".format(key))
        _logger.info("Fetching data about sender from api key")
        data = {
            "apiKey": key,
            "modelName": "Counterparty",
            "calledMethod": "getCounterparties",
            "methodProperties": {
                "CounterpartyProperty": "Sender",
            },
        }
        _logger.debug("Data to send {}".format(data))
        response = APIRequest.get_data(data)

        # """ Запрос происходит в файле utils.
        # Если ошибка - возвращается словарь, если все норм - то список """

        if isinstance(response, dict):
            _logger.error("the data was faulty, answer: {}".format(response))
        else:
            _logger.debug("data was ok, response: {}".format(response))
            vals["senderref"] = response[0]["Ref"]
            vals["sendertype"] = response[0]["Description"]

        data = {
            "apiKey": key,
            "modelName": "Counterparty",
            "calledMethod": "getCounterpartyContactPersons",
            "methodProperties": {"Ref": vals["senderref"], "Page": "1"},
        }

        _logger.debug("Data to send {}".format(data))
        response = APIRequest.get_data(data)
        if isinstance(response, dict):
            _logger.error("the data was faulty, answer: {}".format(response))
        else:
            vals["contacts"] = []
            for sender_contact in response:
                _logger.debug("Creating sender contact: {}".format(sender_contact))
                vals["contacts"].append(
                    (
                        0,
                        0,
                        {
                            "name": sender_contact.get("Description"),
                            "ref": sender_contact.get("Ref"),
                            "phones": sender_contact.get("Phones", None),
                        },
                    )
                )
        return super().create(vals)


class NPSenderContact(models.Model):
    """
        {
            "apiKey": "YourApi",
            "modelName": "Counterparty",
            "calledMethod": "getCounterpartyContactPersons",
            "methodProperties": {
                "Ref": "YourRef"
            }
        }
    "data": [
        {
            "Description": "Surname Name Thirdname",
            "Phones": "YourPhone",
            "Email": "",
            "Ref": "YourRef",
            "LastName": "Surname",
            "FirstName": "Name",
            "MiddleName": "Thirdname"
        }
    ]
    """

    _name = "delivery_novaposhta.sender_contact"
    _inherit = "delivery_novaposhta.base_spreadsheet"

    phones = fields.Char("Phones")
    related_key = fields.Many2one("delivery_novaposhta.api_key")
    related_carrier = fields.Many2one("delivery.carrier")
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        readonly=True,
        default=lambda self: self.env.user.company_id,
    )

    data = {
        "apiKey": "",
        "modelName": "Counterparty",
        "calledMethod": "getCounterpartyContactPersons",
        "methodProperties": {"Ref": ""},
    }
