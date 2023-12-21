from odoo import fields, models


class SOPaymentType(models.Model):
    _inherit = "so.payment.type"

    fiscal_receipt_req = fields.Selection(
        [("yes", "Yes"), ("no", "No"), ("after_receive", "After Receive")],
        default="no",
        string="Fiscal Receipt Required",
    )

    pos_payment_method_id = fields.Many2one(
        comodel_name="pos.payment.method",
        string="POS payment method",
    )
    checkbox_payment_type = fields.Selection(
        [
            ("CASH", "CASH"),
            ("CASHLESS", "CARD"),
        ],
        string="Fiscal Payment Type",
    )
    checkbox_payment_label = fields.Char(
        string="Payment Type Label",
        help="Label for payment type in the POS program",
    )
