# Copyright 2015 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class ReportAction(models.Model):
    _inherit = "ir.actions.report"

    report_type = fields.Selection(
        selection_add=[("docx", "DOCX")], ondelete={"docx": "set default"}
    )

    @api.model
    def _render_docx(self, docids, data):
        report_model = self.env.get("report.report_docx.abstract")
        report_template = self.env["biko.docx.template"].search(
            [("report_action_id", "=", self.id)]
        )
        return (
            report_model.with_context(active_model=self.model)
            .sudo(False)
            .create_docx_report(docids, data, report_template)  # noqa
        )

    @api.model
    def _get_report_from_name(self, report_name):
        res = super()._get_report_from_name(report_name)
        if res:
            return res
        report_obj = self.env["ir.actions.report"]
        qwebtypes = ["docx"]
        conditions = [
            ("report_type", "in", qwebtypes),
            ("report_name", "=", report_name),
        ]
        context = self.env["res.users"].context_get()
        return report_obj.with_context(**context).search(conditions, limit=1)
