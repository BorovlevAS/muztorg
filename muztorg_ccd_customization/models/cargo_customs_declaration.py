from odoo import api, fields, models


class CargoCustomsDeclaration(models.Model):
    _inherit = "cargo.customs.declaration"

    uah_currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="UAH Currency",
        default=lambda self: self.env.ref("base.UAH", raise_if_not_found=False),
    )

    purchase_currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Purchase Currency",
    )
    purchase_currency_rate = fields.Float(string="Purchase Currency Rate")

    customs_fee_uah = fields.Monetary(
        string="Customs fee (UAH)",
        currency_field="uah_currency_id",
    )

    customs_fee = fields.Monetary(
        compute="_compute_customs_fee",
        store=True,
    )

    @api.depends("customs_fee_uah", "date")
    def _compute_customs_fee(self):
        for declaration in self:
            if declaration.uah_currency_id != declaration.company_currency_id:
                declaration.customs_fee = declaration.uah_currency_id._convert(
                    declaration.customs_fee_uah,
                    declaration.company_currency_id,
                    declaration.company_id,
                    declaration.date,
                )
            else:
                declaration.customs_fee = declaration.customs_fee_uah
