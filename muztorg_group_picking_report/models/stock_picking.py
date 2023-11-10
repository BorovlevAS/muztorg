from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def get_move_ids_without_package(self):
        dict = []
        for stock in self:
            if stock.picking_type_id.code in ["outgoing", "internal"]:
                location = stock.location_id.id
            else:
                location = stock.location_dest_id.id
            for move in stock.move_ids_without_package:
                for ml in move.move_line_ids:
                    dict.append(
                        {
                            "state": stock.state,
                            "product_id": ml.product_id,
                            "categ_id": ml.product_id.categ_id,
                            "biko_control_code": ml.product_id.biko_control_code,
                            "product_uom_qty": ml.product_uom_qty,
                            "qty_done": ml.qty_done,
                            "product_uom_id": ml.product_uom_id.name,
                            "qty_available": ml.product_id.with_context(
                                location=location
                            ).qty_available,
                            # "location_id": ml.location_id.id,
                        }
                    )
        return sorted(
            dict,
            # key=lambda x: (x["location_id"]),
            key=lambda x: (
                x["categ_id"],
                x["biko_control_code"],
            ),
        )
