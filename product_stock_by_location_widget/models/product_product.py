import json

from odoo import fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    json_remainings_popover = fields.Char(
        string="JSON data for the popover widget",
        compute="_compute_remaining_popover_data",
    )

    def _compute_remaining_popover_data(self):
        locations = self.env["stock.location"].search(
            [("show_stock_on_products", "=", True)]
        )
        for rec in self:
            data = []
            for location in locations:
                product = rec.with_context(location=location.id)
                data.append(
                    {
                        "complete_name": location.complete_name,
                        "qty_available": "%.2f" % product.qty_available,
                        "virtual_available": "%.2f" % product.virtual_available,
                        "incoming_qty": "%.2f" % product.incoming_qty,
                        "outgoing_qty": "%.2f" % product.outgoing_qty,
                    }
                )

            rec.json_remainings_popover = json.dumps({"remainings": data})
