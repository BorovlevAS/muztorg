from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    stock_reserved_qty = fields.Float(string="Stock Reserved Quantity")

    @api.depends(
        "qty_invoiced",
        "qty_delivered",
        "product_uom_qty",
        "order_id.state",
    )
    def _get_to_invoice_qty(self):
        super()._get_to_invoice_qty()

        for line in self:
            if line.order_id.state in ["waiting", "sale", "done"]:
                if line.product_id.invoice_policy == "order":
                    line.qty_to_invoice = line.product_uom_qty - line.qty_invoiced
                else:
                    line.qty_to_invoice = line.qty_delivered - line.qty_invoiced
            else:
                line.qty_to_invoice = 0

        return True

    def write(self, vals):
        if "product_id" in vals:
            for rec in self:
                stock_move_reservation_ids = self.env["stock.move.reservation"].search(
                    [
                        ("custome_so_line_id", "=", rec.id),
                        ("state", "!=", "cancel"),
                    ]
                )
                stock_move_ids = self.env["stock.move"]
                for move_res in stock_move_reservation_ids:
                    stock_move_ids += move_res.move_id
                if stock_move_ids:
                    result = stock_move_ids._action_cancel()
                    if result:
                        vals.update(stock_reserved_qty=0.0)
        return super().write(vals)

    def unlink(self):
        for rec in self:
            stock = self.env["stock.move.reservation"].search(
                [("custome_so_line_id", "=", rec.id)]
            )
            stock_res_move_ids = stock.mapped("move_id")
            stock_res_move_ids._action_cancel()
            stock.unlink()
        return super().unlink()
