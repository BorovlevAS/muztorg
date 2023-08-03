from odoo import api, models


class CitiesList(models.Model):
    _inherit = "delivery_novaposhta.cities_list"

    @api.model
    def _name_search(
        self, name, args=None, operator="ilike", limit=100, name_get_uid=None
    ):
        search_name = name + ("%" if not name.endswith("%") else "")
        return super()._name_search(
            name=search_name,
            args=args,
            operator="=ilike",
            limit=limit,
            name_get_uid=name_get_uid,
        )
