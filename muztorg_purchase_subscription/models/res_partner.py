# Copyright 2023 Domatix - Carlos Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class Partner(models.Model):
    _inherit = "res.partner"

    subscription_ids = fields.One2many(
        comodel_name="purchase.subscription",
        inverse_name="partner_id",
        string="Subscriptions",
    )
    subscription_count = fields.Integer(
        required=False,
        compute="_compute_subscription_count",
    )

    def _compute_subscription_count(self):
        for record in self:
            record.subscription_count = len(record.subscription_ids)

    def action_view_subscription_ids(self):
        return {
            "type": "ir.actions.act_window",
            "res_model": "purchase.subscription",
            "domain": [("id", "in", self.subscription_ids.ids)],
            "name": self.name,
            "view_mode": "tree,form",
            "context": {
                "default_partner_id": self.id,
            },
        }
