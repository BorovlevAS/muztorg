# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def _generate_product_name(self, vals):
        
        if vals['type'] == 'product':
            brand_name = vals['product_brand_id']
            model_name = vals['biko_product_model']
            prefix_name = vals['biko_product_prefix']

            res = f'{brand_name} {model_name} {prefix_name}'
            
            return res
        else:
            return vals['name']

    @api.onchange('product_brand_id', 'biko_product_prefix', 'biko_product_model')
    def _onchange_product_fields(self):
        for rec in self:
            vals = {
                'type': rec.type,
                'name': rec.name,
                'product_brand_id': rec.product_brand_id.name.strip().upper() if rec.product_brand_id else '',
                'biko_product_model': rec.biko_product_model.strip().upper() if rec.biko_product_model else '',
                'biko_product_prefix': rec.biko_product_prefix.name.strip().upper() if rec.biko_product_prefix else '',
            }
            rec.name = self._generate_product_name(vals)

    def _gen_vals(self, iscreation, vals):

        product_brand_id = self.env['product.brand'].browse([vals.get('product_brand_id', 
            self.product_brand_id.id if not iscreation else '')])

        if product_brand_id and product_brand_id.name:
            product_brand_name = product_brand_id.name.strip().upper()
        else:
            product_brand_name = ''

        biko_product_model = vals.get('biko_product_model', 
            self.biko_product_model if not iscreation else '')

        biko_product_model = biko_product_model.strip().upper() if biko_product_model else ''

        biko_product_prefix_id = vals.get('biko_product_prefix', self.biko_product_prefix.id if not iscreation else '')
        biko_product_prefix = self.env['biko.product.prefix'].browse([biko_product_prefix_id])

        if biko_product_prefix and biko_product_prefix.name:
            biko_product_prefix_name = biko_product_prefix.name.strip().upper()
        else:
            biko_product_prefix_name = ''

        gen_vals = {
            'type': vals.get('type', self.type),
            'name': vals.get('name', self.name),
            'product_brand_id': product_brand_name,
            'biko_product_model': biko_product_model,
            'biko_product_prefix': biko_product_prefix_name,
        }

        return gen_vals

    @api.model
    def create(self, vals):
        
        gen_vals = self._gen_vals(iscreation=True, vals=vals)

        vals['name'] = self._generate_product_name(gen_vals)
 
        return super(ProductTemplate, self).create(vals)

    def write(self, vals):
        
        gen_vals = self._gen_vals(iscreation=False, vals=vals)

        vals['name'] = self._generate_product_name(gen_vals)

        return super(ProductTemplate, self).write(vals)
