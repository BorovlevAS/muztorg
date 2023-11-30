from odoo import fields, models


class ReturnPicking(models.TransientModel):
    _inherit = "stock.return.picking"

    biko_reason_return = fields.Char(
        "Reason for return",
        required=True,
    )

    def _create_returns(self):
        """in this function the picking is marked as return"""
        new_picking, pick_type_id = super()._create_returns()
        picking = self.env["stock.picking"].browse(new_picking)
        picking.write({"biko_reason_return": self.biko_reason_return})
        return new_picking, pick_type_id
