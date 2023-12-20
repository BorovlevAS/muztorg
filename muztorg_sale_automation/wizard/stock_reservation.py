from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class StockReservation(models.TransientModel):
    _name = "stock.reservation"

    sale_order_id = fields.Many2one(
        "sale.order",
        string="Sale Order",
        readonly=True,
    )
    reservation_line_ids = fields.One2many(
        "stock.reservation.line",
        "reservation_id",
        string="Reservation Line",
    )
    user_ids = fields.Many2many(
        "res.users",
        string="Email Notification",
    )

    def action_create_reservation(self):
        def get_qty_by_locations(product_id, warehouse_id, product_qty):
            if not warehouse_id.stock_reservation_order_id:
                picking_type_id = picking_type_obj.search(
                    [
                        (
                            "warehouse_id",
                            "=",
                            warehouse_id.id,
                        ),
                        ("code", "=", "outgoing"),
                    ],
                    limit=1,
                )
                return {picking_type_id.default_location_src_id: product_qty}
            else:
                result = {}
                need_to_reserve = product_qty
                for line in warehouse_id.stock_reservation_order_id.line_ids:
                    product_quant_loc = product_id.with_context(
                        location=line.location_id.id
                    ).qty_available
                    if product_quant_loc >= need_to_reserve:
                        result.update({line.location_id: need_to_reserve})
                        break
                    elif product_quant_loc > 0.0:
                        result.update({line.location_id: product_quant_loc})
                        need_to_reserve -= product_quant_loc
                return result

        self.ensure_one()
        custome_reservtion_obj = self.env["stock.move.reservation"]
        picking_type_obj = self.env["stock.picking.type"]

        for line in self.reservation_line_ids:
            if (
                line.stock_reservation_qty > 0.0
                and line.product_qty >= line.stock_reservation_qty
            ):
                order_line_reserve_qty = line.order_line_id.stock_reserved_qty
                order_line_reserve_qty += line.stock_reservation_qty

                if line.order_line_id.product_uom_qty >= order_line_reserve_qty:
                    location_dest_id = self.env["stock.location"].search(
                        [
                            ("is_stock_location_reservation", "=", True),
                            (
                                "company_id",
                                "=",
                                self.sale_order_id.company_id.id,
                            ),
                        ],
                        limit=1,
                    )
                    qty_by_locations = get_qty_by_locations(
                        line.product_id,
                        self.sale_order_id.warehouse_id,
                        line.stock_reservation_qty,
                    )
                    reserve_move_ids = []
                    for (
                        location_id,
                        qty_to_reserve,
                    ) in qty_by_locations.items():
                        reserv_move_id = custome_reservtion_obj.create(
                            {
                                "name": self.sale_order_id.name,
                                "custome_so_line_id": line.order_line_id.id,
                                "product_id": line.product_id.id,
                                "product_uom_qty": qty_to_reserve,
                                "product_uom": line.uom_id.id,
                                "location_id": location_id.id,
                                "location_dest_id": location_dest_id.id,
                                "custome_sale_order_id": self.sale_order_id.id,
                                "reserv_request_date": fields.Datetime.now(),
                                "reserv_resquest_user_id": self.env.uid,
                            }
                        )

                        if reserv_move_id:
                            line.order_line_id.stock_reserved_qty += qty_to_reserve
                            self.sale_order_id.is_stock_reserv_created = True
                            # reserv_move_id.move_id._action_confirm()
                            reserve_move_ids.append(reserv_move_id.move_id.id)

                    self.env["stock.move"].browse(reserve_move_ids)._action_confirm()
                else:
                    raise ValidationError(_("All the quantities are reserved"))


class StockReservationLine(models.TransientModel):
    _name = "stock.reservation.line"

    reservation_id = fields.Many2one(
        "stock.reservation",
        string="Reservation",
    )
    sale_order_id = fields.Many2one(
        "sale.order",
        string="Sale Order",
        related="reservation_id.sale_order_id",
        store=True,
    )
    order_line_id = fields.Many2one(
        "sale.order.line",
        string="Sale Order Line",
        required=True,
        ondelete="cascade",
        domain=lambda self: [
            ("order_id", "=", self._context.get("current_sale_order_id"))
        ],
    )
    product_id = fields.Many2one(
        "product.product",
        string="Product",
    )
    product_qty = fields.Float(
        string="Quantity",
    )
    stock_reservation_qty = fields.Float(
        string="Reservation Quantity",
        required=True,
    )
    uom_id = fields.Many2one(
        #        'product.uom',
        "uom.uom",
        string="UOM",
    )

    @api.onchange("order_line_id")
    def _onchange_order_line_id(self):
        self.product_id = self.order_line_id.product_id.id
        self.product_qty = self.order_line_id.product_uom_qty
        self.uom_id = self.order_line_id.product_uom.id
