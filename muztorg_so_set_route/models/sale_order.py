from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"
    
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:            
            if vals.get("carrier_id") and vals.get("warehouse_id"):
                carrier_id = self.env["delivery.carrier"].browse(vals["carrier_id"])
                warehouse_id = self.env["stock.warehouse"].browse(vals["warehouse_id"])
                if warehouse_id.biko_carrier_ids and carrier_id in warehouse_id.biko_carrier_ids:
                    vals["route_id"] = warehouse_id.biko_route_id.id
        return super().create(vals_list)

    @api.onchange("warehouse_id")
    def _onchange_warehouse_id(self):
        for rec in self:            
            if rec.warehouse_id.biko_carrier_ids and rec.carrier_id in rec.warehouse_id.biko_carrier_ids:
                rec.route_id = rec.warehouse_id.biko_route_id

    @api.onchange("carrier_id")
    def _onchange_carrier_id(self):
        for rec in self:            
            if rec.warehouse_id.biko_carrier_ids and rec.carrier_id in rec.warehouse_id.biko_carrier_ids:
                rec.route_id = rec.warehouse_id.biko_route_id
