# наследовать модель product.product
# добавить зависимое поле biko_control_code
# добавить поиск по biko_control_code
from odoo import api, fields, models

class ProductProduct(models.Model):
    _inherit = "product.product"

    biko_control_code = fields.Char(
        string="Control code",
        related="product_tmpl_id.biko_control_code",
        store=True,
    )

    @api.model
    def _name_search(
        self, name, args=None, operator="ilike", limit=100, name_get_uid=None
    ):
        if not args:
            args = []
        if name:
            product_ids = list(
                self._search(
                    [("biko_control_code", "=", name)] + args,
                    limit=limit,
                    access_rights_uid=name_get_uid,
                )
            )

            if not product_ids:
                return super(ProductProduct, self)._name_search(
                    name,
                    args,
                    operator=operator,
                    limit=limit,
                    name_get_uid=name_get_uid,
                )

        else:

            return super(ProductProduct, self)._name_search(
                name, args, operator=operator, limit=limit, name_get_uid=name_get_uid
            )