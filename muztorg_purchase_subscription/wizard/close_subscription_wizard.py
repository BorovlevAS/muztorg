# Copyright 2023 Domatix - Carlos Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class CloseSubscriptionWizard(models.TransientModel):
    _name = "close.reason.wizard"
    _description = "Close reason wizard"

    close_reason_id = fields.Many2one(
        comodel_name="purchase.subscription.close.reason", string="Reason"
    )

    def button_confirm(self):
        purchase_subscription = self.env["purchase.subscription"].browse(
            self.env.context["active_id"]
        )
        purchase_subscription.close_reason_id = self.close_reason_id.id
        stage = purchase_subscription.stage_id
        closed_stage = self.env["purchase.subscription.stage"].search(
            [("type", "=", "post")], limit=1
        )
        if stage != closed_stage:
            purchase_subscription.stage_id = closed_stage
            purchase_subscription.active = False
