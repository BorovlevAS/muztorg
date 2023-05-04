from odoo import fields, models


class Lead(models.Model):
    _inherit = "crm.lead"

    product_name = fields.Char(string="Product Name")
    product_serial = fields.Char(string="Product Serial")
    garanty_type = fields.Selection(
        selection=[("guarantee", "Guarantee"), ("non_guarantee", "Non guarantee")]
    )
    complexity = fields.Text(string="Coplexity")
    malfunction = fields.Text(string="Malfunction")
    pick_up_point = fields.Many2one("biko.pickup.point", string="Pickup Point")
    pick_out_point = fields.Many2one("biko.pickup.point", string="Pickout Point")
    maintenance_point = fields.Many2one(
        "biko.maintenance.points", string="Maintenance Point"
    )
    TTN = fields.Char(string="TTN")
    np_info = fields.Char(string="NP Info")
    dealer_info_date = fields.Date(string="Order Date")
    dealer_info_order = fields.Char(string="Order Number")
