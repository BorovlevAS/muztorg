from odoo import fields, models


class StockWarehouse(models.Model):
    _inherit = "stock.warehouse"

    is_delivery_set_to_done = fields.Boolean(string="Is Delivery Set to Done")
    create_invoice = fields.Selection(
        selection=[
            ("on_confirm", "On confirm sale order"),
            ("on_waiting_for_payment", "On waiting for payment"),
        ],
        string="When to create an invoice?",
    )
    validate_invoice = fields.Boolean(string="Validate invoice?")
