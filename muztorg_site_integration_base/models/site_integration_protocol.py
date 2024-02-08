import base64

from odoo import _, api, fields, models


class SiteIntegrationProtocol(models.Model):
    _name = "site.integration.protocol"
    _inherit = ["mail.thread"]

    name = fields.Char(compute="_compute_name")
    date_exchange = fields.Datetime()
    settings_id = fields.Many2one(comodel_name="site.integration.base")
    status = fields.Selection(
        [("ok", "No errors"), ("error", "With errors")],
        default="ok",
    )
    note = fields.Text()

    @api.depends("date_exchange", "settings_id")
    def _compute_name(self):
        for rec in self:
            rec.name = (
                rec.settings_id.name
                + _(" of ")
                + rec.date_exchange.strftime("%Y-%m-%d %H:%M:%S")
            )

    def create_file(self, data):
        self.ensure_one()
        attachments = self.env["ir.attachment"]
        attachments |= self.env["ir.attachment"].create(
            {
                "name": "exchange",
                "res_id": self.id,
                "res_model": "site.integration.protocol",
                "datas": base64.b64encode(data),
                "type": "binary",
                # 'type': False,
                "mimetype": "text/xml",
            }
        )
        if attachments:
            self.message_post(attachment_ids=attachments.ids)
