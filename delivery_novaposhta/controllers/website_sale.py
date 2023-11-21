from odoo import http
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.http import request


class WebsiteSaleDelivery(WebsiteSale):
    @http.route(
        ["/shop/address"],
        type="http",
        methods=["GET", "POST"],
        auth="public",
        website=True,
    )
    def address(self, **kw):
        res = super().address(**kw)
        cities = request.env["delivery_novaposhta.cities_list"].search([])
        streets = request.env["delivery_novaposhta.streets_list"].search([])
        res.qcontext.update(
            {
                "cities": cities,
                "streets": streets,
            }
        )
        return res
