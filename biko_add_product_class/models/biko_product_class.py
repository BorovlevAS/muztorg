# -*- coding: utf-8 -*-
from odoo import models, fields, api

class BikoProductClass(models.Model):
    _name = 'biko.product.class'
    _order = 'name'

    name = fields.Char(string='Name')