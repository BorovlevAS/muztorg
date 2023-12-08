from odoo import api, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.depends("qty_invoiced", "qty_delivered", "product_uom_qty", "order_id.state")
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
