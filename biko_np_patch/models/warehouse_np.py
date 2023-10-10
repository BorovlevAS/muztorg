from odoo import api, models


class NovaPoshtaWarehouse(models.Model):
    _inherit = "delivery_novaposhta.warehouse"

    @api.model
    def _name_search(
        self, name, args=None, operator="ilike", limit=100, name_get_uid=None
    ):
        if name:
            args = args + [("number", "=", name)]
        return super()._name_search(
            name=name,
            args=args,
            operator=operator,
            limit=limit,
            name_get_uid=name_get_uid,
        )
