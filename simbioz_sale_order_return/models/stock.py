from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    sale_stock_return_id = fields.Many2one(
        comodel_name="sale.stock.return",
        string="Sale stock return (nnt)",
        ondelete="restrict",
    )


class StockMove(models.Model):
    _inherit = "stock.move"

    qty_returnable = fields.Float(
        digits="Product Unit of Measure",
        string="Returnable Quantity",
        compute="_compute_qty_returnable",
        readonly=True,
        store=True,
    )

    @api.depends(
        "state",
        "returned_move_ids",
        "returned_move_ids.state",
        "quantity_done",
        "reserved_availability",
        "returned_move_ids.qty_returnable",
    )
    def _compute_qty_returnable(self):
        """Looks for chained returned moves to compute how much quantity
        from the original can be returned"""
        for move in self.filtered(lambda x: x.state in ["draft", "cancel"]):
            move.qty_returnable = 0.0

        for move in self.filtered(lambda x: x.state not in ["draft", "cancel"]):
            if not move.returned_move_ids:
                if move.state == "done":
                    move.qty_returnable = move.quantity_done
                else:
                    move.qty_returnable = move.reserved_availability
                continue
            move.returned_move_ids._compute_qty_returnable()
            move.qty_returnable = move.quantity_done - sum(
                move.returned_move_ids.mapped("qty_returnable")
            )
