from odoo import api, fields, models


class StockRequestOrder(models.Model):
    _inherit = "stock.request.order"

    biko_route_id = fields.Many2one(
        "stock.location.route",
        string="Route",
        domain="[('id', 'in', biko_route_ids), ('stock_request_selectable', '=', True)]",
        ondelete="restrict",
    )

    biko_route_ids = fields.Many2many(
        "stock.location.route",
        string="Routes",
        compute="_compute_biko_route_ids",
        readonly=True,
    )

    biko_picking_ids = fields.One2many(
        comodel_name="stock.picking",
        inverse_name="stock_request_order_id",
        string="Transfers",
    )

    biko_picking_count = fields.Integer(
        string="Delivery Orders", compute="_compute_biko_picking_ids", readonly=True
    )

    @api.depends("biko_picking_ids")
    def _compute_biko_picking_ids(self):
        for record in self:
            record.biko_picking_count = len(record.biko_picking_ids)

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

    @api.onchange("biko_route_id")
    def _onchange_biko_route_id(self):
        self.change_childs()

    def change_childs(self):
        if not self._context.get("no_change_childs", False):
            for line in self.stock_request_ids:
                line.warehouse_id = self.warehouse_id
                line.location_id = self.location_id
                line.company_id = self.company_id
                line.picking_policy = self.picking_policy
                line.expected_date = self.expected_date
                line.requested_by = self.requested_by
                line.procurement_group_id = self.procurement_group_id
                line.route_id = self.biko_route_id

    def _prepare_procurement_group_vals(self):
        return {
            "name": self.name,
            "move_type": self.picking_policy,
            "stock_request_order_id": self.id,
        }

    def action_confirm(self):
        for rec in self:
            if not rec.procurement_group_id:
                rec.with_context(no_change_childs=True).procurement_group_id = self.env[
                    "procurement.group"
                ].create(rec._prepare_procurement_group_vals())
                for line in self.stock_request_ids:
                    line.procurement_group_id = rec.procurement_group_id

        return super().action_confirm()

    def action_cancel(self):
        self.mapped("biko_picking_ids").action_cancel()
        self.mapped("stock_request_ids").write({"state": "cancel"})
        return True

    def action_view_delivery(self):
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "stock.action_picking_tree_all"
        )

        pickings = self.mapped("biko_picking_ids")
        if len(pickings) > 1:
            action["domain"] = [("id", "in", pickings.ids)]
        elif pickings:
            action["views"] = [(self.env.ref("stock.view_picking_form").id, "form")]
            action["res_id"] = pickings.id
        return action
