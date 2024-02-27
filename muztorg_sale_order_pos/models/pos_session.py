import requests

from odoo import _, models


class PosSession(models.Model):
    _inherit = "pos.session"

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
