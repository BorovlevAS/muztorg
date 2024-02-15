from odoo import api, fields, models


class CargoCustomsDeclarationLine(models.Model):
    _inherit = "cargo.customs.declaration.line"

    uah_currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="UAH Currency",
        related="customs_section_id.uah_currency_id",
    )

    customs_amount_uah = fields.Monetary(
        string="Customs Amount (UAH)",
        compute="_compute_customs_amount_uah",
        inverse="_inverse_customs_amount_uah",
        help="Customs Amount in UAH",
        currency_field="uah_currency_id",
        store=True,
    )
    duty_amount = fields.Monetary(
        compute="_compute_duty_amount",
        store=True,
    )
    excide_tax_amount = fields.Monetary(
        compute="_compute_excide_tax_amount",
        store=True,
    )

    duty_amount_uah = fields.Monetary(
        string="Duty Amount (UAH)",
        currency_field="uah_currency_id",
    )
    excide_tax_amount_uah = fields.Monetary(
        string="Excide Tax Amount (UAH)",
        currency_field="uah_currency_id",
    )
    vat_amount_uah = fields.Monetary(
        string="VAT Amount (UAH)",
        compute="_compute_vat_amount_uah",
        currency_field="uah_currency_id",
        store=True,
    )

    @api.depends(
        "duty_amount_uah",
        "customs_section_id.customs_declaration_id.date",
    )
    def _compute_duty_amount(self):
        for line in self:
            if line.uah_currency_id != line.currency_id:
                line.duty_amount = line.uah_currency_id._convert(
                    line.duty_amount_uah,
                    line.currency_id,
                    line.company_id,
                    line.customs_section_id.customs_declaration_id.date,
                )
            else:
                line.duty_amount = line.duty_amount_uah

    @api.depends(
        "excide_tax_amount_uah",
        "customs_section_id.customs_declaration_id.date",
    )
    def _compute_excide_tax_amount(self):
        for line in self:
            if line.uah_currency_id != line.currency_id:
                line.excide_tax_amount = line.uah_currency_id._convert(
                    line.excide_tax_amount_uah,
                    line.currency_id,
                    line.company_id,
                    line.customs_section_id.customs_declaration_id.date,
                )
            else:
                line.excide_tax_amount = line.excide_tax_amount_uah

    @api.depends(
        "customs_amount_po_curr",
        "po_currency_id",
        "customs_amount_uah",
        "customs_section_id.customs_declaration_id.date",
    )
    def _compute_customs_amount(self):
        for line in self:
            if line.uah_currency_id != line.currency_id:
                line.customs_amount = line.uah_currency_id._convert(
                    line.customs_amount_uah,
                    line.currency_id,
                    line.company_id,
                    line.customs_section_id.customs_declaration_id.date,
                )
            else:
                line.customs_amount = line.customs_amount_uah

    @api.depends(
        "vat_amount_uah",
        "customs_section_id.customs_declaration_id.date",
    )
    def _compute_vat_amount(self):
        for line in self:
            if line.uah_currency_id != line.currency_id:
                line.vat_amount = line.uah_currency_id._convert(
                    line.vat_amount_uah,
                    line.currency_id,
                    line.company_id,
                    line.customs_section_id.customs_declaration_id.date,
                )
            else:
                line.vat_amount_uah = line.vat_amount_uah

    @api.depends(
        "customs_amount_po_curr",
        "po_currency_id",
        "customs_section_id.customs_declaration_id.date",
    )
    def _compute_customs_amount_uah(self):
        for line in self:
            if line.po_currency_id != line.uah_currency_id:
                line.customs_amount_uah = (
                    line.customs_amount_po_curr
                    * line.customs_declaration_id.purchase_currency_rate
                )
            else:
                line.customs_amount_uah = line.customs_amount_po_curr

    def _inverse_customs_amount_uah(self):
        for line in self:
            if line.po_currency_id != line.uah_currency_id:
                line.customs_amount_po_curr = (
                    line.customs_amount_uah
                    / line.customs_declaration_id.purchase_currency_rate
                    if line.customs_declaration_id.purchase_currency_rate
                    else 0.0
                )
            else:
                line.customs_amount_po_curr = line.customs_amount_uah

    @api.depends(
        "product_qty",
        "customs_amount_uah",
        "tax_ids",
        "duty_amount_uah",
        "excide_tax_amount_uah",
    )
    def _compute_vat_amount_uah(self):
        for line in self:
            taxes = line.tax_ids.compute_all(
                price_unit=line.customs_amount_uah
                + line.duty_amount_uah
                + line.excide_tax_amount_uah,
                currency=line.uah_currency_id,
                product=line.product_id,
            )
            line.update(
                {
                    "vat_amount_uah": sum(
                        t_line.get("amount", 0.0) for t_line in taxes.get("taxes", [])
                    ),
                }
            )
