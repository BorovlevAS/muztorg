from odoo import models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def _load_records(self, data_list, update=False):
        return super()._load_records(data_list=data_list, update=update)
