from odoo import api, fields, models


class PosConfig(models.Model):
    _inherit = "pos.config"

    checkbox_mode = fields.Selection(
        selection_add=[
            ("checkbox_kassa", "Checkbox Kassa"),
        ],
        ondelede={"checkbox_kassa": "set default"},
    )
    checkbox_url = fields.Char(
        string="Checkbox url",
        compute="_compute_checkbox_url",
        inverse="_inverse_checkbox_url",
        store=True,
    )

    checkbox_port = fields.Integer(string="Checkbox port")

    @api.depends("checkbox_mode")
    def _compute_checkbox_url(self):
        for rec in self:
            if rec.checkbox_mode == "prod":
                rec.checkbox_url = "https://api.checkbox.in.ua"
            elif rec.checkbox_mode == "dev":
                rec.checkbox_url = "https://dev-api.checkbox.in.ua"
            else:
                rec.checkbox_url = "127.0.0.1"

    def _inverse_checkbox_url(self):
        pass
