# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class StockRequestOrder(models.Model):
    _inherit = "stock.request.order"

    biko_route_id = fields.Many2one(
        "stock.location.route",
        string="Route",
        domain="[('id', 'in', biko_route_ids)]",
        ondelete="restrict",
    )

    biko_route_ids = fields.Many2many(
        "stock.location.route",
        string="Routes",
        compute="_compute_biko_route_ids",
        readonly=True,
    )

    @api.depends("warehouse_id", "location_id")
    def _compute_biko_route_ids(self):
        route_obj = self.env["stock.location.route"]
        routes = route_obj.search(
            [("warehouse_ids", "in", self.mapped("warehouse_id").ids)]
        )
        routes_by_warehouse = {}
        for route in routes:
            for warehouse in route.warehouse_ids:
                routes_by_warehouse.setdefault(
                    warehouse.id, self.env["stock.location.route"]
                )
                routes_by_warehouse[warehouse.id] |= route
        for record in self:
            routes = route_obj
            if record.warehouse_id and routes_by_warehouse.get(record.warehouse_id.id):
                routes |= routes_by_warehouse[record.warehouse_id.id]
            parents = record.get_parents().ids
            record.biko_route_ids = routes.filtered(
                lambda r, parents=parents: any(
                    p.location_id.id in parents for p in r.rule_ids
                )
            )

    def get_parents(self):
        location = self.location_id
        result = location
        while location.location_id:
            location = location.location_id
            result |= location
        return result
