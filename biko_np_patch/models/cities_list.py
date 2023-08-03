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

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        for record in domain:
            if isinstance(record, list) and ("ilike" in record):
                search_name = record[2] + ("%" if not record[2].endswith("%") else "")
                record[2] = search_name
                record[1] = "=ilike"

        return super().search_read(
            domain=domain,
            fields=fields,
            offset=offset,
            limit=limit,
            order=order,
        )
