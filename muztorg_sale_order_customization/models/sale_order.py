from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    biko_website_ref = fields.Char("Website Order #")
    biko_1c_ref = fields.Char("1C Order #")
    so_payment_type_id = fields.Many2one(
        comodel_name="so.payment.type",
        string="Payment Type",
        copy=False,
    )

    biko_1c_currency = fields.Integer()

    def recalculate_prices(self):
        if len(self) > 1:
            return

        record = self

        if not record.biko_1c_currency:
            return

        company_id = record.company_id
        pricelist_uah = company_id.biko_uah_pricelist_id
        from_curr = record.pricelist_id.currency_id
        to_curr = pricelist_uah.currency_id

        if from_curr == to_curr:
            return

        record.write({"pricelist_id": pricelist_uah.id})

    @api.model_create_multi
    def create(self, vals_list):
        result = super().create(vals_list)

        for record in result:
            record.recalculate_prices()

        return result

    def action_confirm(self):
        self.write({"user_id": self.env.user.id})
        for record in self:
            wh_before = record.warehouse_id
            record.onchange_user_id()
            record.warehouse_id = wh_before
        return super().action_confirm()

    def _action_cancel(self):
        self.check_pickings_before_cancel()
        self.check_invoice_before_cancel()
        result = super()._action_cancel()
        if result:
            inv = self.invoice_ids.filtered(
                lambda inv: inv.state == "posted" and inv.payment_state == "not_paid"
            )
            inv.button_draft()
            inv.button_cancel()
        return result

    def check_invoice_before_cancel(self):
        for record in self:
            if record.invoice_ids.filtered(
                lambda inv: inv.state == "posted" and inv.payment_state != "not_paid"
            ):
                raise ValidationError(
                    _(
                        "There are already paid invoices for this sale order. You cannot cancel it."
                    )
                )

    def check_pickings_before_cancel(self):
        for record in self:
            #  all pickings are not done
            if all(
                state not in ["done"] for state in record.picking_ids.mapped("state")
            ):
                return True

            out_pickings = record.picking_ids.filtered(
                lambda rec: rec.location_dest_id.usage == "customer"
            )
            # we have at least one customer-picking done
            if any(state == "done" for state in out_pickings.mapped("state")):
                raise ValidationError(
                    _(
                        "There are already done pickings for this sale order. You cannot cancel it."
                    )
                )
            # check inter-warehouse transfers
            internal_wh_pickings = record.picking_ids.filtered(
                lambda rec: rec.location_dest_id.usage == "internal"
                and rec.state not in ["done", "cancel"]
            )
            if not internal_wh_pickings:
                return True

            raise ValidationError(
                _(
                    "There are internal transfers, that are not done. Please, cancel or validate them first."
                )
            )
        return True
