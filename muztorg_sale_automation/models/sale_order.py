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

    stock_move_ids = fields.One2many(
        comodel_name="stock.move.reservation",
        inverse_name="custome_sale_order_id",
        string="Stock Reservations",
        copy=False,
    )

    is_stock_reserv_created = fields.Boolean(string="Is Stock Created", copy=False)

    def create_reservation(self):
        reservation_id = self.env["stock.reservation"].create(
            [{"sale_order_id": self.id}]
        )
        for line_id in self.order_line:
            self.env["stock.reservation.line"].create(
                [
                    {
                        "reservation_id": reservation_id.id,
                        "order_line_id": line_id.id,
                        "product_id": line_id.product_id.id,
                        "product_qty": line_id.product_uom_qty,
                        "uom_id": line_id.product_uom.id,
                        "stock_reservation_qty": line_id.product_uom_qty,
                    }
                ]
            )
        reservation_id.action_create_reservation()
        return True

    def action_set_waiting(self):
        self.create_reservation()
        res = self.write({"state": "waiting"})
        for order in self:
            self.process_invoices(order, "on_waiting_for_payment")
        return res

    def action_draft(self):
        result = super().action_draft()
        for order_id in self:
            if order_id.state == "waiting":
                order_id.cancel_stock_reservation()
                order_id.write(
                    {
                        "state": "draft",
                        "signature": False,
                        "signed_by": False,
                        "signed_on": False,
                    }
                )
        return result

    def action_cancel_stock_reservation(self):
        self.ensure_one()
        order_line_ids = self.order_line
        stock_move_reservation_ids = self.env["stock.move.reservation"].search(
            [
                ("custome_so_line_id", "in", order_line_ids.ids),
                ("state", "!=", "cancel"),
            ]
        )
        stock_move_ids = self.env["stock.move"]
        for move_res in stock_move_reservation_ids:
            stock_move_ids += move_res.move_id
        if stock_move_ids:
            result = stock_move_ids._action_cancel()
            if result:
                order_line_ids.write(
                    {
                        "stock_reserved_qty": 0.0,
                    }
                )
                self.is_stock_reserv_created = False
            return {
                "type": "ir.actions.client",
                "tag": "reload",
            }
        else:
            if not self._context.get("is_unlink_reserved_stock"):
                return {
                    "type": "ir.actions.client",
                    "tag": "reload",
                }

    def cancel_stock_reservation(self):
        result = self.action_cancel_stock_reservation()
        self.state = "draft"
        return result

    def action_confirm(self):
        for order in self:
            order_line = order.order_line
            stock_move_reservation_ids = self.env["stock.move.reservation"].search(
                [
                    ("custome_so_line_id", "in", order_line.ids),
                    ("state", "!=", "cancel"),
                ]
            )
            if stock_move_reservation_ids:
                self.action_cancel_stock_reservation()
        res = super().action_confirm()

        for order in self:
            self.process_pickings(order)
            self.process_invoices(order, "on_confirm")

        return res

    def action_cancel(self):
        self.ensure_one()
        order_line_ids = self.order_line
        stock_move_reservation_ids = self.env["stock.move.reservation"].search(
            [
                ("custome_so_line_id", "in", order_line_ids.ids),
            ]
        )
        if stock_move_reservation_ids:
            self.with_context(
                is_unlink_reserved_stock=True
            ).action_cancel_stock_reservation()
            stock_move_reservation_ids.unlink()
        return super().action_cancel()

    def action_view_reserved_stock(self):
        self.ensure_one()
        action = (
            self.env.ref("muztorg_sale_automation.action_stock_move_reserv_product")
            .sudo()
            .read()[0]
        )
        action["domain"] = [("id", "in", self.stock_move_ids.ids)]
        return action

    def schedule_action_cancel_reservation(self):
        return True
        # nb_days = 0
        # if self.env["number.days.reservation"].search([])[0]:
        #     nb_days = self.env["number.days.reservation"].search([])[0].nb_days
        # date_obj = (fields.datetime.now()) - relativedelta(hours=int(nb_days * 24))
        # reservations = self.env["stock.move.reservation"].search(
        #     [
        #         ("reserv_request_date", "<=", date_obj),
        #         ("state", "!=", "cancel"),
        #     ]
        # )
        # for reserve in reservations:
        #     reserve.custome_sale_order_id.action_cancel_stock_reservation()

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
