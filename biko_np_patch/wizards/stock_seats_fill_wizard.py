from odoo import fields, models


class StockPickingFillWizard(models.TransientModel):
    _name = "stock.picking.fill.wizard"
    stock_picking_id = fields.Many2one(comodel_name="stock.picking")
    picking_seats_ids = fields.One2many(related="stock_picking_id.picking_seats_ids")

    def action_apply(self):
        pass
