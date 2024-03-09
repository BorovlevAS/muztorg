import ast

from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    sale_stock_return_id = fields.One2many(
        comodel_name="sale.stock.return",
        inverse_name="sale_order_id",
        string="Sale stock return (nnt)",
    )

    def _prepare_return_order_vals(self):
        return {
            "company_id": self.company_id.id,
            "currency_id": self.currency_id.id,
            "partner_id": self.partner_id.id,
            "contract_id": self.contract_id.id,
            "sale_order_id": self.id,
            "location_id": self.warehouse_id.lot_stock_id.id,
            "line_ids": [],
        }

    def action_create_return_order(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "simbioz_sale_order_return.sale_stock_return_action"
        )
        action["views"] = [
            (
                self.env.ref(
                    "simbioz_sale_order_return.sale_stock_return_view_form"
                ).id,
                "form",
            )
        ]

        action["context"] = {
            **ast.literal_eval(action["context"]),
        }

        order_vals = self._prepare_return_order_vals()

        for order_line in self.order_line.filtered(
            lambda line: line.product_id.type in ["product", "consu"]
            and not line.display_type
            and (line.qty_delivered or line.qty_invoiced)
        ):
            order_line_vals = order_line._prepare_return_order_line_vals()
            order_vals["line_ids"].append((0, 0, order_line_vals))

        for key, value in order_vals.items():
            action["context"][f"default_{key}"] = value

        return action

    def action_view_return(self):
        record_ids = self.mapped("sale_stock_return_id")
        action = self.env["ir.actions.actions"]._for_xml_id(
            "simbioz_sale_order_return.sale_stock_return_action"
        )
        if len(record_ids) > 1:
            action["domain"] = [("id", "in", record_ids.ids)]
        elif len(record_ids) == 1:
            form_view = [
                (
                    self.env.ref(
                        "simbioz_sale_order_return.sale_stock_return_view_form"
                    ).id,
                    "form",
                )
            ]
            if "views" in action:
                action["views"] = form_view + [
                    (state, view) for state, view in action["views"] if view != "form"
                ]
            else:
                action["views"] = form_view
            action["res_id"] = record_ids.id
        else:
            action = {"type": "ir.actions.act_window_close"}

        return action


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    sale_stock_return_line_ids = fields.One2many(
        comodel_name="sale.stock.return.line",
        inverse_name="sale_order_line_id",
        string="Sale stock return lines (nnt)",
    )

    def _prepare_return_order_line_vals(self):
        return {
            "sale_order_line_id": self.id,
        }
