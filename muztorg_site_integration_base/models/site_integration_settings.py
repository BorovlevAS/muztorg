from odoo import _, fields, models


class SiteIntegrationBase(models.Model):
    _name = "site.integration.base"

    name = fields.Char(string="Name")
    # setting_pickup_id = fields.Many2one(string="Pickup", comodel_name="delivery.carrier")
    # setting_nova_poshta_id = fields.Many2one(
    #     string="Nova poshta", comodel_name="delivery.carrier"
    # )
    # setting_warehouse_podol_id = fields.Many2one(
    #     string="Warehouse Podol", comodel_name="stock.warehouse"
    # )
    url = fields.Char()
    active = fields.Boolean()
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        default=lambda self: self.env.company,
    )

    def sync_call(self):
        self.ensure_one()
        vals = {"settings_id": self.id, "url": self.url}
        si_sync = self.env["site.integration.sync"].create(vals)

        return {
            "name": _("sync"),
            "res_model": "site.integration.sync",
            "res_id": si_sync.id,
            "type": "ir.actions.act_window",
            "view_id": False,
            "view_mode": "form",
            "view_type": "form",
            "target": "new",
        }
