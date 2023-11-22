from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    biko_default_sale_workflow_id = fields.Many2one(
        comodel_name="sale.workflow.process",
        string="Default Automatic Workflow for Sale Order",
    )


class Settings(models.TransientModel):
    _inherit = "res.config.settings"
    biko_default_sale_workflow_id = fields.Many2one(
        comodel_name="sale.workflow.process",
        related="company_id.biko_default_sale_workflow_id",
        string="Default Automatic Workflow for Sale Order",
        readonly=False,
    )
