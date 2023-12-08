from odoo import _, api, fields, models


class StockMovereservation(models.Model):
    _name = "stock.move.reservation"
    _inherits = {"stock.move": "move_id"}

    reserv_code = fields.Char(
        string="Reservation Code",
        default="New",
        copy=False,
        readonly=True,
    )
    move_id = fields.Many2one(
        "stock.move",
        "Reservation Move",
        required=True,
        readonly=True,
        ondelete="cascade",
    )
    custome_so_line_id = fields.Many2one(
        "sale.order.line",
        string="Order Line",
        copy=False,
        readonly=True,
        ondelete="cascade",
    )
    custome_sale_order_id = fields.Many2one(
        "sale.order",
        string="Sale Order",
        copy=False,
        readonly=True,
    )
    reserv_request_date = fields.Datetime(
        string="Request for Reservation",
        copy=False,
        readonly=True,
    )
    reserv_resquest_user_id = fields.Many2one(
        "res.users",
        string="Request for Reservation By",
        copy=False,
        readonly=True,
    )

    @api.model
    def create(self, vals):
        if vals.get("reserv_code", _("New")) == _("New"):
            vals["reserv_code"] = self.env["ir.sequence"].next_by_code(
                "stock.move.reservation"
            ) or _("New")
        return super().create(vals)


class StockLocation(models.Model):
    _inherit = "stock.location"

    is_stock_location_reservation = fields.Boolean(
        string="Is Stock Location Reservation ?",
        copy=False,
    )
