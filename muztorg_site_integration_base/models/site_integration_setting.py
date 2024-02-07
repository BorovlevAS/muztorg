from transliterate import translit

from odoo import api, fields, models


class SiteIntegrationSetting(models.Model):
    _name = "site.integration.setting"

    # _TTYPE_SELECTION = [
    #     ("boolean", "boolean"),
    #     ("char", "char"),
    #     # ("date", "date"),
    #     # ("datetime", "datetime"),
    #     # ("float", "float"),
    #     # ("integer", "integer"),
    #     ("many2one", "many2one"),
    #     # ("selection", "selection"),
    # ]

    name = fields.Char(string="Parameter")

    # setting_id = fields.Many2one(comodel_name="site.integration.base")

    id_seting = fields.Char(
        compute="_compute_id_seting",
        store=True,
        # readonly=False,
    )

    # model_reference = fields.Reference(
    #     string="Value",
    #     # compute="_compute_origin_values",
    #     selection="_reference_models",
    #     # readonly=True
    # )
    # value_many2one = fields.Reference(
    #     string="Value",
    #     # compute="_compute_origin_values",
    #     selection="_reference_models",
    #     # readonly=True
    # )

    # value_char = fields.Char(
    #     # compute="_compute_origin_values",
    #     # readonly=True
    # )
    # value_date = fields.Date(
    #     # compute="_compute_origin_values",
    #     # readonly=True
    #     )
    # value_datetime = fields.Datetime(
    #     # compute="_compute_origin_values",
    #     # readonly=True
    #     )
    # value_float = fields.Float(
    #     # compute="_compute_origin_values",
    #     # readonly=True
    #     )
    # value_boolean = fields.Boolean(
    #     # compute="_compute_origin_values",
    #     # readonly=True
    # )

    # ttype = fields.Selection(
    #     string="Field Type",
    #     selection=_TTYPE_SELECTION,
    #     # help="Type of the"
    #     # " Odoo field that will be created. Keep empty if you don't want to"
    #     # " create a new field. If empty, this field will not be displayed"
    #     # " neither available for search or group by function",
    # )

    # @api.model
    # def _reference_models(self):
    #     # models = self.env["ir.model"].search([]) добавила отбор по конкретнім моделям, бо задолбало
    #     models = self.env["ir.model"].search([("model", "in", self.get_model_names())])
    #     return [(model.model, model.name) for model in models]

    # @api.model
    # def get_model_names(self):
    #     return [
    #         "delivery.carrier",
    #         "crm.team",
    #         "stock.warehouse",
    #         "product.pricelist",
    #     ]

    @api.onchange("name")
    def _compute_id_seting(self):
        if self.name:
            latin_text = (
                translit(self.name.strip(), "uk", reversed=True)
                .lower()
                .replace(" ", "_")
            )
            self.id_seting = "id_" + latin_text
