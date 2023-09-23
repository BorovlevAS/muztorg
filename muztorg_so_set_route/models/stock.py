# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class StockWarehouse(models.Model):
    _inherit = "stock.warehouse"

    biko_route_id = fields.Many2one("stock.location.route", string="Route")
    biko_carrier_ids = fields.Many2many(
        comodel_name="delivery.carrier",
        string="Delivery Method",
        # relation="stock_warehouse_carrier_rel",
        # column1="warehouse_id",
        # column2="carrier_id",
    )
