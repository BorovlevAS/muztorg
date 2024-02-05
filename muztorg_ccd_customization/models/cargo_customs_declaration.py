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

    @api.depends("company_id", "state", "purchase_currency_id")
    def _compute_allowed_picking_ids(self):
        allowed_picking_states = ["in_customs"]
        cancelled_ccd = self.env["cargo.customs.declaration"].search_read(
            [("state", "=", "cancel")], ["id"]
        )
        cancelled_ccd_ids = [declaration["id"] for declaration in cancelled_ccd]

        for declaration in self:
            domain_states = list(allowed_picking_states)
            domain = [
                ("company_id", "=", declaration.company_id.id),
                ("purchase_id.currency_id", "=", declaration.purchase_currency_id.id),
                ("immediate_transfer", "=", False),
                ("state", "in", domain_states),
                ("partner_id", "=", declaration.partner_id.id),
                "|",
                "|",
                ("customs_declaration_ids", "=", False),
                ("customs_declaration_ids", "in", declaration.id),
                ("customs_declaration_ids", "in", cancelled_ccd_ids),
            ]

            declaration.allowed_picking_ids = self.env["stock.picking"].search(domain)

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
