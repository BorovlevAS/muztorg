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
    purchase_currency_rate = fields.Float(
        string="Purchase Currency Rate", digits=(12, 6)
    )

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

    def _generate_landed_costs(self):
        for record in self.with_context(skip_account_move_synchronization=True):
            if record.landed_cost_ids:
                record.landed_cost_ids.unlink()

            customs_fee_coef = (
                record.customs_fee / record.customs_amount_total
                if record.customs_amount_total
                else 0
            )
            landed_costs = []
            for line in record.ccd_lines_ids:
                if (
                    not line.duty_amount
                    and not line.excide_tax_amount
                    and not customs_fee_coef
                ):
                    continue

                landed_cost = self.env["stock.landed.cost"].create(
                    {
                        "date": record.date,
                        "picking_ids": [(6, 0, [line.move_line_id.picking_id.id])],
                        "cost_lines": [],
                    }
                )

                landed_costs.append(landed_cost.id)

                adjustment_lines = []

                if line.duty_amount:
                    cost_line = self.env["stock.landed.cost.lines"].create(
                        {
                            "name": record.company_id.ccd_duty_product_id.name,
                            "cost_id": landed_cost.id,
                            "product_id": record.company_id.ccd_duty_product_id.id,
                            "price_unit": line.duty_amount,
                            "split_method": "by_current_cost_price",
                            "account_id": record.company_id.ccd_customs_duty_account_id.id,
                        },
                    )

                    landed_cost["cost_lines"] = [(4, cost_line.id)]

                    val_vals = {
                        "cost_id": landed_cost.id,
                        "cost_line_id": cost_line.id,
                        "move_id": line.move_line_id.id,
                        "product_id": line.product_id.id,
                        "quantity": line.product_qty,
                        "former_cost": sum(
                            line.move_line_id.stock_valuation_layer_ids.mapped("value")
                        ),
                        "additional_landed_cost": line.duty_amount,
                    }

                    adjustment_lines.append((0, 0, val_vals))

                if line.excide_tax_amount:
                    cost_line = self.env["stock.landed.cost.lines"].create(
                        {
                            "name": record.company_id.ccd_excise_product_id.name,
                            "cost_id": landed_cost.id,
                            "product_id": record.company_id.ccd_excise_product_id.id,
                            "price_unit": line.excide_tax_amount,
                            "split_method": "by_current_cost_price",
                            "account_id": record.company_id.ccd_customs_excide_account_id.id,
                        },
                    )

                    landed_cost["cost_lines"] = [(4, cost_line.id)]

                    val_vals = {
                        "cost_id": landed_cost.id,
                        "cost_line_id": cost_line.id,
                        "move_id": line.move_line_id.id,
                        "product_id": line.product_id.id,
                        "quantity": line.product_qty,
                        "former_cost": sum(
                            line.move_line_id.stock_valuation_layer_ids.mapped("value")
                        ),
                        "additional_landed_cost": line.excide_tax_amount,
                    }

                    adjustment_lines.append((0, 0, val_vals))

                if line.vat_amount:
                    cost_line = self.env["stock.landed.cost.lines"].create(
                        {
                            "name": record.company_id.ccd_vat_product_id.name,
                            "cost_id": landed_cost.id,
                            "product_id": record.company_id.ccd_vat_product_id.id,
                            "price_unit": line.vat_amount,
                            "split_method": "by_current_cost_price",
                            "account_id": record.company_id.uavat_account_id.id,
                        },
                    )

                    landed_cost["cost_lines"] = [(4, cost_line.id)]

                    val_vals = {
                        "cost_id": landed_cost.id,
                        "cost_line_id": cost_line.id,
                        "move_id": line.move_line_id.id,
                        "product_id": line.product_id.id,
                        "quantity": line.product_qty,
                        "former_cost": sum(
                            line.move_line_id.stock_valuation_layer_ids.mapped("value")
                        ),
                        "additional_landed_cost": line.vat_amount,
                    }

                    adjustment_lines.append((0, 0, val_vals))

                if customs_fee_coef:
                    cost_line = self.env["stock.landed.cost.lines"].create(
                        {
                            "name": record.company_id.ccd_broker_product_id.name,
                            "cost_id": landed_cost.id,
                            "product_id": record.company_id.ccd_broker_product_id.id,
                            "price_unit": line.customs_amount * customs_fee_coef,
                            "split_method": "by_current_cost_price",
                            "account_id": record.customs_fee_account_id.id,
                        },
                    )

                    landed_cost["cost_lines"] = [(4, cost_line.id)]

                    val_vals = {
                        "cost_id": landed_cost.id,
                        "cost_line_id": cost_line.id,
                        "move_id": line.move_line_id.id,
                        "product_id": line.product_id.id,
                        "quantity": line.product_qty,
                        "former_cost": sum(
                            line.move_line_id.stock_valuation_layer_ids.mapped("value")
                        ),
                        "additional_landed_cost": line.customs_amount
                        * customs_fee_coef,
                    }
                    adjustment_lines.append((0, 0, val_vals))

                landed_cost["valuation_adjustment_lines"] = adjustment_lines

            record.landed_cost_ids = [(6, 0, landed_costs)]
