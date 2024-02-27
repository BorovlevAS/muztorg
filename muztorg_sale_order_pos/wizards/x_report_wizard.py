from odoo import fields, models


class XReportWizard(models.TransientModel):
    _name = "xreport.wizard"
    _description = "X-report wizard"

    report_data = fields.Text(string="Report data", readonly=True)
