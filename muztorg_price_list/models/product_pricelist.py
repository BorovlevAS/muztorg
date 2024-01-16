from odoo import _, fields, models


class Pricelist(models.Model):
    _inherit = "product.pricelist"

    def import_file_call(self):
        self.ensure_one()
        vals = {"price_id": self.id}
        pl_import = self.env["price.list.import"].create(vals)

        return {
            "name": _("Attachments"),
            "res_model": "price.list.import",
            "res_id": pl_import.id,
            "type": "ir.actions.act_window",
            "view_id": False,
            "view_mode": "form",
            "view_type": "form",
            "target": "new",
        }

    def remove_old_discount_prices(self):
        self.ensure_one()
        date = fields.Datetime.today()
        for line in self.item_ids:
            if line.date_end and line.date_end < date:
                line.unlink()
        return {
            "type": "ir.actions.client",
            "tag": "reload",
        }
