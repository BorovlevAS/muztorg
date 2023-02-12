# -*- coding: utf-8 -*-
from odoo import models, fields, api

from random import randint

class BikoProductClass(models.Model):
    _name = 'biko.product.prefix'
    _order = 'name'

    name = fields.Char(string='Name')

    def _get_default_color(self):
        return randint(1, 11)

    color = fields.Integer(string='Color Index', default=_get_default_color)