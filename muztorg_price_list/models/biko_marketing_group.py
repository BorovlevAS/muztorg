from odoo import fields, models


class MarketingGroup(models.Model):
    _name = "biko.marketing.group"
    _order = "name"

    name = fields.Char(string="Name")
    limit_from = fields.Float(digits=(6, 4), string="From")
    limit_to = fields.Float(digits=(6, 4), string="To")
