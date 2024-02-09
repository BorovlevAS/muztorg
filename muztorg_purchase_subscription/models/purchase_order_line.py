# Copyright 2023 Domatix - Carlos Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    def get_subscription_line_values(self):
        return {
            "product_id": self.product_id.id,
            "name": self.product_id.name,
            "product_uom_qty": self.product_uom_qty,
            "price_unit": self.price_unit,
            "price_subtotal": self.price_subtotal,
        }
