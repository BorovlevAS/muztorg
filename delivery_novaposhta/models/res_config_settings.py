from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    company_share_np_key = fields.Boolean(
        "Share np key to all companies",
        help="Share your np key to all companies defined in your instance.\n"
        " * Checked : Key are visible for every company, even if a company is defined on the partner.\n"
        " * Unchecked : Each company can see only its key (key where company is defined). \n"
        " Key not related to a company are visible for all companies.",
    )
    company_share_np_ttn = fields.Boolean(
        "Share np TTN to all companies",
        help="Share your np TTN to all companies defined in your instance.\n"
        " * Checked : TTN are visible for every company, even if a company is defined on the partner.\n"
        " * Unchecked : Each company can see only its TTN (TTN where company is defined).\n"
        " TTN not related to a company are visible for all companies.",
    )
    company_share_np_sender = fields.Boolean(
        "Share np sender to all companies",
        help="Share your np sender to all companies defined in your instance.\n"
        " * Checked : sender are visible for every company, even if a company is defined on the partner.\n"
        " * Unchecked : Each company can see only its sender (sender where company is defined).\n"
        " sender not related to a company are visible for all companies.",
    )

    @api.model
    def get_values(self):
        res = super().get_values()
        key_rule = self.env.ref("delivery_novaposhta.np_comp_rule_key")
        ttn_rule = self.env.ref("delivery_novaposhta.np_comp_rule_ttn")
        sender_rule = self.env.ref("delivery_novaposhta.np_comp_rule_sender")
        res.update(
            company_share_np_key=not bool(key_rule.active),
            company_share_np_ttn=not bool(ttn_rule.active),
            company_share_np_sender=not bool(sender_rule.active),
        )
        return res

    def set_values(self):
        # pylint: disable=missing-return
        super().set_values()
        key_rule = self.env.ref("delivery_novaposhta.np_comp_rule_key")
        key_rule.write({"active": not bool(self.company_share_np_key)})
        ttn_rule = self.env.ref("delivery_novaposhta.np_comp_rule_ttn")
        ttn_rule.write({"active": not bool(self.company_share_np_ttn)})
        sender_rule = self.env.ref("delivery_novaposhta.np_comp_rule_sender")
        sender_rule.write({"active": not bool(self.company_share_np_sender)})
