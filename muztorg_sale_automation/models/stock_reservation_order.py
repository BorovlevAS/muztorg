from odoo import fields, models


class StockReservationOrder(models.Model):
    _name = "stock.reservation.order"
    _description = "Stock Reservation Order"

    name = fields.Char(string="Name", required=True, copy=False)
    line_ids = fields.One2many(
        comodel_name="stock.reservation.order.line",
        inverse_name="stock_reservation_order_id",
        string="Lines",
    )


class StockReservationOrderLine(models.Model):
    _name = "stock.reservation.order.line"
    _description = "Stock Reservation Order Line"

    _rec_name = "location_id"

    stock_reservation_order_id = fields.Many2one(comodel_name="stock.reservation.order")
    sequence = fields.Integer(string="Sequence")
    location_id = fields.Many2one(
        comodel_name="stock.location",
        required=True,
        string="Location",
        domain="[('usage','=','internal')]",
    )
