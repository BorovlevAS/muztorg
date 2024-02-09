# Copyright 2023 Domatix - Carlos Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class PurchaseSubscriptionCloseReason(models.Model):
    _name = "purchase.subscription.close.reason"
    _description = "Close reason model"

    name = fields.Char(required=True)
