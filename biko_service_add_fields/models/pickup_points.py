from odoo import models, fields


class PickUpPoint(models.Model):
    _name = "biko.pickup.point"
    _description = "Pickup Point"

    name = fields.Char(string="Name", required=True, translate=True)


class MeintenancePoints(models.Model):
    _name = "biko.maintenance.points"
    _description = "Maintenance Points"

    name = fields.Char(string="Name", required=True, translate=True)
