from odoo import fields, models


class SOPaymentType(models.Model):
    _name = "so.payment.type"
    _description = "Sale Order Payment Type"

    _rec_name = "name"
    _order = "sequence"

    active = fields.Boolean(string="Active", default=True)

    name = fields.Char(string="Name", required=True, copy=False)

    is_prepayment = fields.Boolean(string="Is Prepayment")
    sequence = fields.Integer(string="Sequence")
    website_ref = fields.Char(string="Website Ref")
