# -*- coding: utf-8 -*-
from odoo import models, fields, api

class BikoProductClass(models.Model):
    _name = 'biko.product.prefix'
    _order = 'name'

    name = fields.Char(string='Name')