from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    enable_vendor_code_uniq = fields.Boolean(
        string="Enable the uniqueness of Vendor Code field",
        config_parameter="biko_add_product_class.enable_vendor_code_uniq",
        help="When this setting is set, when a user creates new product "
        "the system will check the uniqueness of the vendor code",
    )

    def set_values(self):
        res = super().set_values()
        self.env["ir.config_parameter"].sudo().set_param(
            "enable_vendor_code_uniq", self.enable_vendor_code_uniq
        )

        return res

    @api.model
    def get_values(self):
        res = super().get_values()
        params = self.env["ir.config_parameter"].sudo()
        enable_vendor_code_uniq = params.get_param(
            "enable_vendor_code_uniq", default=False
        )
        res.update(enable_vendor_code_uniq=enable_vendor_code_uniq)
        return res
