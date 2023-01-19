from odoo import models, fields, api

class BikoModelClass(models.Model):
    _name = 'biko.product.model'
    _order = 'name'

    name = fields.Char(string='Name')