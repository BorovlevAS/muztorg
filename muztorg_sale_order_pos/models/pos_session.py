import requests

from odoo import _, fields, models


class PosSession(models.Model):
    _inherit = "pos.session"

    return_order_counter = fields.Integer(
        string="RO count", compute="_compute_return_order_counter"
    )

    def _compute_return_order_counter(self):
        for record in self:
            record.return_order_counter = self.env["sale.stock.return"].search_count(
                [("pos_session_id", "=", record.id)]
            )

    def get_related_return_orders(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "simbioz_sale_order_return.sale_stock_return_action"
        )
        action["domain"] = [("pos_session_id", "=", self.id)]
        return action

    def action_print_x_report(self):
        self.ensure_one()
        if not self.config_id.use_checkbox:
            return False

        response = requests.post(
            self.config_id.checkbox_url + "/api/v1/reports",
            headers={
                "Accept": "application/json;",
                "Authorization": "Bearer " + self.checkbox_access_token,
            },
            timeout=5,
        )

        response_json = response.json()
        if not response_json.get("id", False):
            return False

        report_id = response_json["id"]
        response = requests.get(
            self.config_id.checkbox_url + f"/api/v1/reports/{report_id}/text",
            headers={
                "Accept": "application/json;",
                "Authorization": "Bearer " + self.checkbox_access_token,
            },
            timeout=5,
        )

        if not response.ok:
            return False

        report_text = response.text

        wizard = self.env["xreport.wizard"].create(
            {
                "report_data": report_text,
            }
        )

        view = self.env.ref("muztorg_sale_order_pos.xreport_wizard_view_form")

        return {
            "name": _("X-Report"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "xreport.wizard",
            "views": [(view.id, "form")],
            "view_id": view.id,
            "target": "new",
            "res_id": wizard.id,
        }