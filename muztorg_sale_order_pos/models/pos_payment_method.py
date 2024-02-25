from odoo import fields, models


class PosPaymentMethod(models.Model):
    _inherit = "pos.payment.method"

    cash_journal_id = fields.Many2one(
        comodel_name="account.journal",
        domain=[("type", "in", ("cash", "bank"))],
        string="Journal",
    )
