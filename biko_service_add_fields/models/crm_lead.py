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
    comment = fields.Text(string="Comment")
    dealer_info = fields.Text(string="Date an Order Info")
