from odoo import http
from odoo.http import request


class NovaPoshtaNotification(http.Controller):
    @http.route(["/event/notification/<i>"], type="http", auth="public")
    def event_notification(self, i, **post):
        if i == "send":
            res = request.env["delivery_novaposhta.notification"].send()
        else:
            res = False
        return res
