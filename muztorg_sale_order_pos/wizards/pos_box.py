from odoo import _, api, fields

from odoo.addons.checkbox_integration.wizard.pos_box import PosCheckbox


class BikoPosCheckbox(PosCheckbox):
    _register = False

    in_out = fields.Selection(
        [("in", "In"), ("out", "Out")],
        string="Type",
        required=True,
        default="in",
    )
    amount_user = fields.Float(string="Amount", digits=0, required=True)


class PosBoxOut(BikoPosCheckbox):
    _inherit = "cash.box.out"

    @api.onchange("in_out", "amount_user")
    def _onchange_in_out(self):
        for record in self:
            record.name = _("Cash Out") if record.in_out == "out" else _("Cash In")
            record.amount = (
                record.amount_user if record.in_out == "in" else -record.amount_user
            )
