from odoo import api, fields, models


class SalePosPaymentLine(models.Model):
    _name = "sale.pos.payment.line"
    _description = "Sale Payment - POS Payment correspondence"

    _rec_name = "name"
    _order = "name ASC"

    name = fields.Char(
        string="Name",
        compute="_compute_name",
        store=True,
    )

    sale_order_payment_id = fields.Many2one(
        comodel_name="so.payment.type",
        string="Sale Order Payment",
    )

    pos_payment_method_id = fields.Many2one(
        comodel_name="pos.payment.method",
        string="POS Payment Method",
    )

    pos_config_id = fields.Many2one(
        comodel_name="pos.config",
        string="POS Config (nnt)",
    )

    @api.depends("sale_order_payment_id", "pos_payment_method_id")
    def _compute_name(self):
        for record in self:
            record.name = "{} - {}".format(
                record.sale_order_payment_id.name, record.pos_payment_method_id.name
            )
