from odoo import api, fields, models, tools, _


class PickingCancelWizard(models.TransientModel):
    _inherit = "picking.cancel.wizard"

    reason_id = fields.Many2one("picking.cancel.reasons", string="Reason", required=False)
    reason = fields.Text(string="Comment", required=False)
