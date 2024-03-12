from odoo import api, fields, models
from odoo.tools.float_utils import float_is_zero


class StockPicking(models.Model):
    _inherit = "stock.picking"

    biko_reason_return = fields.Char(
        "Reason for return",
    )


class StockMove(models.Model):
    _inherit = "stock.move"

    @api.model
    def get_excluded_location_types(self):
        return ["supplier", "inventory", "customer", "production", "transit"]

    @api.depends("move_line_ids.product_qty")
    def _compute_reserved_availability(self):  # pylint: disable=W8110
        super()._compute_reserved_availability()
        excluded_location_types = self.get_excluded_location_types()

        if not any(self._ids):
            # onchange
            for move in self:
                reserved_availability = 0
                for ml in move.move_line_ids:
                    reserved_availability += ml.product_qty
                    if (
                        ml.product_id.tracking == "serial"
                        and float_is_zero(
                            ml.product_qty,
                            precision_rounding=ml.product_uom_id.rounding,
                        )
                        and ml.location_id.usage not in excluded_location_types
                        and not (
                            ml.location_id.usage == "internal"
                            and ml.location_dest_id.usage == "internal"
                        )
                    ):
                        reserved_availability += ml.qty_done
                move.reserved_availability = move.product_id.uom_id._compute_quantity(
                    reserved_availability, move.product_uom, rounding_method="HALF-UP"
                )
        else:
            # compute
            grouped_data = self.env["stock.move.line"].read_group(
                [("move_id", "in", self.ids)],
                ["move_id", "product_qty", "qty_done"],
                ["move_id"],
            )
            result = {}
            for data in grouped_data:
                move_id = self.env["stock.move"].browse(data["move_id"][0])
                product_qty = data["product_qty"]
                qty_done = data["qty_done"]

                result[move_id.id] = data["product_qty"]
                if (
                    float_is_zero(
                        product_qty, precision_rounding=move_id.product_uom.rounding
                    )
                    and move_id.product_id.tracking == "serial"
                    and move_id.location_id.usage not in excluded_location_types
                    and not (
                        move_id.location_id.usage == "internal"
                        and move_id.location_dest_id.usage == "internal"
                    )
                ):
                    result[move_id.id] += qty_done
            for move in self:
                move.reserved_availability = move.product_id.uom_id._compute_quantity(
                    result.get(move.id, 0.0),
                    move.product_uom,
                    rounding_method="HALF-UP",
                )
