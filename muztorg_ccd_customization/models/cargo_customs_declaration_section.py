from odoo import api, fields, models


class CargoCustomsDeclarationSection(models.Model):
    _inherit = "cargo.customs.declaration.section"

    uah_currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="UAH Currency",
        related="customs_declaration_id.uah_currency_id",
    )

    customs_amount_uah = fields.Monetary(
        string="Customs Amount (UAH)",
        currency_field="uah_currency_id",
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
        currency_field="uah_currency_id",
    )

    customs_amount = fields.Monetary(
        compute="_compute_customs_amount",
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
    vat_amount = fields.Monetary(
        compute="_compute_vat_amount",
        store=True,
    )

    @api.depends("customs_amount_uah", "customs_declaration_id.date")
    def _compute_customs_amount(self):
        for section in self:
            if section.uah_currency_id != section.currency_id:
                section.customs_amount = section.uah_currency_id._convert(
                    section.customs_amount_uah,
                    section.currency_id,
                    section.company_id,
                    section.customs_declaration_id.date,
                )
            else:
                section.customs_amount = section.customs_amount_uah

    @api.depends("duty_amount_uah", "customs_declaration_id.date")
    def _compute_duty_amount(self):
        for section in self:
            if section.uah_currency_id != section.currency_id:
                section.duty_amount = section.uah_currency_id._convert(
                    section.duty_amount_uah,
                    section.currency_id,
                    section.company_id,
                    section.customs_declaration_id.date,
                )
            else:
                section.duty_amount = section.duty_amount_uah

    @api.depends("excide_tax_amount_uah", "customs_declaration_id.date")
    def _compute_excide_tax_amount(self):
        for section in self:
            if section.uah_currency_id != section.currency_id:
                section.excide_tax_amount = section.uah_currency_id._convert(
                    section.excide_tax_amount_uah,
                    section.currency_id,
                    section.company_id,
                    section.customs_declaration_id.date,
                )
            else:
                section.excide_tax_amount = section.excide_tax_amount_uah

    @api.depends("vat_amount_uah", "customs_declaration_id.date")
    def _compute_vat_amount(self):
        for section in self:
            if section.uah_currency_id != section.currency_id:
                section.vat_amount = section.uah_currency_id._convert(
                    section.vat_amount_uah,
                    section.currency_id,
                    section.company_id,
                    section.customs_declaration_id.date,
                )
            else:
                section.vat_amount = section.vat_amount_uah

    @api.onchange(
        "customs_amount_uah",
        "duty_amount_uah",
        "excide_tax_amount_uah",
        "vat_amount_uah",
        "tax_ids",
    )
    def _onchange_customs_amount(self):
        for line in self:
            taxes = line.tax_ids.compute_all(
                price_unit=line.customs_amount_uah
                + line.duty_amount_uah
                + line.excide_tax_amount_uah,
                currency=line.uah_currency_id,
            )
            line.update(
                {
                    "vat_amount_uah": sum(
                        t_line.get("amount", 0.0) for t_line in taxes.get("taxes", [])
                    ),
                }
            )

    @api.onchange("duty_rate", "customs_amount_uah")
    def _onchange_duty_rate(self):
        for line in self:
            line.duty_amount_uah = line.duty_rate / 100 * line.customs_amount_uah

    @api.onchange("duty_amount_uah")
    def _onchange_duty_amount(self):
        for line in self:
            line.duty_rate = (
                line.duty_amount_uah / line.customs_amount_uah * 100
                if line.customs_amount_uah
                else 0
            )

    @api.onchange("excide_tax_rate")
    def _onchange_excide_tax_rate(self):
        for line in self:
            line.excide_tax_amount_uah = (
                line.excide_tax_rate / 100 * line.customs_amount_uah
            )

    @api.onchange("excide_tax_amount_uah", "customs_amount_uah")
    def _onchange_excide_tax_amount(self):
        for line in self:
            line.excide_tax_rate = (
                line.excide_tax_amount_uah / line.customs_amount_uah * 100
                if line.customs_amount_uah
                else 0
            )

    def action_calc_by_products(self):
        for section in self:
            customs_amount = sum(section.mapped("line_ids.customs_amount") or [0])
            customs_amount_uah = sum(
                section.mapped("line_ids.customs_amount_uah") or [0]
            )
            duty_amount = sum(section.mapped("line_ids.duty_amount") or [0])
            duty_amount_uah = sum(section.mapped("line_ids.duty_amount_uah") or [0])
            excide_tax_amount = sum(section.mapped("line_ids.excide_tax_amount") or [0])
            excide_tax_amount_uah = sum(
                section.mapped("line_ids.excide_tax_amount_uah") or [0]
            )
            vat_amount = sum(section.mapped("line_ids.vat_amount") or [0])
            vat_amount_uah = sum(section.mapped("line_ids.vat_amount_uah") or [0])
            tax_ids = [(6, 0, set(section.mapped("line_ids.tax_ids")._ids))]

            section.customs_amount_uah = customs_amount_uah
            section.customs_amount = customs_amount
            section.duty_amount_uah = duty_amount_uah
            section.duty_amount = duty_amount
            section.duty_rate = (
                100 * duty_amount_uah / customs_amount_uah if customs_amount_uah else 0
            )
            section.excide_tax_amount_uah = excide_tax_amount_uah
            section.excide_tax_amount = excide_tax_amount
            section.excide_tax_rate = (
                100 * excide_tax_amount_uah / customs_amount_uah
                if customs_amount_uah
                else 0
            )
            section.vat_amount_uah = vat_amount_uah
            section.vat_amount = vat_amount
            section.tax_ids = tax_ids

    def action_distrib_among_products(self):
        self.ensure_one()

        customs_amount_total = 0
        max_cat_ids = 0
        max_customs_amount = 0
        coef_values = {}

        for idx, line in enumerate(self.line_ids):
            customs_amount_total += line.customs_amount_uah
            max_cat_ids = (
                idx if line.customs_amount_uah > max_customs_amount else max_cat_ids
            )
            coef_values.update({line.id: line.customs_amount_uah})

        if customs_amount_total == 0:
            return

        customs_amount_rest = self.customs_amount_uah
        coef_customs_amount = customs_amount_rest / customs_amount_total
        duty_amount_rest = self.duty_amount_uah
        coef_duty_amount = duty_amount_rest / customs_amount_total
        excide_tax_amount_rest = self.excide_tax_amount_uah
        coef_excide_tax_amount = excide_tax_amount_rest / customs_amount_total
        vat_amount_rest = self.vat_amount_uah
        coef_vat_amount = vat_amount_rest / customs_amount_total

        for line in self.line_ids:
            line.customs_amount_uah = coef_values.get(line.id, 0) * coef_customs_amount
            customs_amount_rest -= line.customs_amount_uah
            line.duty_amount_uah = coef_values.get(line.id, 0) * coef_duty_amount
            duty_amount_rest -= line.duty_amount_uah
            line.excide_tax_amount_uah = (
                coef_values.get(line.id, 0) * coef_excide_tax_amount
            )
            excide_tax_amount_rest -= line.excide_tax_amount_uah
            line.vat_amount_uah = coef_values.get(line.id, 0) * coef_vat_amount
            vat_amount_rest -= line.vat_amount_uah
            line.tax_ids = [(6, 0, set(self.tax_ids._ids))]

        self.line_ids[max_cat_ids].customs_amount_uah += customs_amount_rest
        self.line_ids[max_cat_ids].duty_amount_uah += duty_amount_rest
        self.line_ids[max_cat_ids].excide_tax_amount_uah += excide_tax_amount_rest
        self.line_ids[max_cat_ids].vat_amount_uah += vat_amount_rest
