from odoo import api, fields, models


class SiteIntegrationSettingLine(models.Model):
    _name = "site.integration.setting.line"

    _TTYPE_SELECTION = [
        ("boolean", "boolean"),
        ("char", "char"),
        # ("date", "date"),
        # ("datetime", "datetime"),
        # ("float", "float"),
        # ("integer", "integer"),
        ("many2one", "many2one"),
        # ("selection", "selection"),
    ]

    name = fields.Char()

    settings_id = fields.Many2one(comodel_name="site.integration.base")
    setting_id = fields.Many2one(comodel_name="site.integration.setting")

    id_seting = fields.Char(
        # compute="_compute_id_seting",
        related="setting_id.id_seting",
        store=True,
    )

    value_many2one = fields.Reference(
        string="Value",
        # related="setting_id.value_many2one",
        selection="_reference_models",
    )

    @api.model
    def _reference_models(self):
        # models = self.env["ir.model"].search([]) добавила отбор по конкретнім моделям, бо задолбало
        models = self.env["ir.model"].search([("model", "in", self.get_model_names())])
        return [(model.model, model.name) for model in models]

    @api.model
    def get_model_names(self):
        return [
            "delivery.carrier",
            "crm.team",
            "stock.warehouse",
            "product.pricelist",
            "crm.stage",
        ]
