# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def _generate_product_name(self):
        self.ensure_one()

        if self.type == 'product':
            if self.product_brand_id.name:
                brand_name = self.product_brand_id.name.strip().capitalize()
            else:
                brand_name = ''

            if self.biko_product_model:
                model_name = self.biko_product_model.strip().capitalize()
            else:
                model_name = ''

            if self.biko_product_prefix.name:
                prefix_name = self.biko_product_prefix.name.strip().capitalize()
            else:
                prefix_name = ''

            return f'{brand_name} {model_name} {prefix_name}'
        else:
            return self.name

    @api.onchange('product_brand_id', 'biko_product_prefix', 'biko_product_model')
    def _onchange_product_fields(self):
        for rec in self:
            rec.name = self._generate_product_name()

    def write(self, vals):
        
        vals['name'] = self._generate_product_name()

        return super(ProductTemplate, self).write(vals)
