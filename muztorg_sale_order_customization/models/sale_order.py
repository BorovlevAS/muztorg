import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


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

        for order_line in record.order_line:
            price_unit = from_curr._convert(
                order_line["price_unit"],
                to_curr,
                company_id,
                record.date_order,
            )
            _logger.info(
                "MUZTORG_SALE_ORDER_CUSTOMIZATION: {old_price} -> {new_price}".format(
                    old_price=order_line["price_unit"],
                    new_price=price_unit,
                )
            )
            order_line.write({"price_unit": price_unit})

        record.with_context(skip_recalculation_currency=True).write(
            {"pricelist_id": pricelist_uah.id}
        )

    @api.model_create_multi
    def create(self, vals_list):
        result = super().create(vals_list)

        for record in result:
            record.recalculate_prices()

        return result

    def write(self, vals):
        result = super().write(vals)

        if not self.env.context.get("skip_recalculation_currency", False):
            for record in self:
                record.recalculate_prices()

        return result
