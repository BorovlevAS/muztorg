from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    state = fields.Selection(
        selection_add=[
            ("waiting", "Waiting for payment"),
            ("sent",),
        ],
        ondelete={
            "waiting": "set default",
        },
    )

    def action_draft(self):
        super().action_draft()
        orders = self.filtered(lambda s: s.state in ["waiting"])
        return orders.write(
            {
                "state": "draft",
                "signature": False,
                "signed_by": False,
                "signed_on": False,
            }
        )

    def process_invoices(self, order, state_to_check):
        warehouse = order.warehouse_id

        if (
            warehouse.create_invoice == state_to_check
            and not order.invoice_ids.filtered(lambda s: s.state == "posted")
        ):
            order._create_invoices()

        if warehouse.validate_invoice and order.invoice_ids:
            for invoice in order.invoice_ids.filtered(lambda s: s.state == "draft"):
                invoice.action_post()

    def process_pickings(self, order):
        warehouse = order.warehouse_id
        if warehouse.is_delivery_set_to_done and order.picking_ids:
            for picking in self.picking_ids:
                picking.action_assign()
                picking.action_confirm()
                for mv in picking.move_ids_without_package:
                    mv.quantity_done = mv.product_uom_qty
                picking.button_validate()

    def action_set_waiting(self):
        res = self.write({"state": "waiting"})
        for order in self:
            self.process_invoices(order, "on_waiting_for_payment")
        return res

    def action_confirm(self):
        res = super().action_confirm()
        for order in self:
            self.process_pickings(order)
            self.process_invoices(order, "on_confirm")

        return res
