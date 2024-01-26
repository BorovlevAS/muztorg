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

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("biko_1c_currency"):
                _logger.info(
                    "MUZTORG_SALE_ORDER_CUSTOMIZATION: biko_1c_currency: empty field"
                )
                continue

            if not vals.get("company_id", False):
                _logger.info(
                    "MUZTORG_SALE_ORDER_CUSTOMIZATION: company_id: empty field"
                )
                continue

            if not vals.get("order_line", False):
                _logger.info(
                    "MUZTORG_SALE_ORDER_CUSTOMIZATION: order_line: empty field"
                )
                continue

            company_id = self.env["res.company"].browse(vals["company_id"])
            pricelist_uah = company_id.biko_uah_pricelist_id

            if (
                vals.get("pricelist_id", False)
                and vals["pricelist_id"] == pricelist_uah.id
            ):
                _logger.info(
                    "MUZTORG_SALE_ORDER_CUSTOMIZATION: pricelist_id: empty or equal to UAH pricelist"
                )
                continue

            from_curr = (
                self.env["product.pricelist"].browse(vals["pricelist_id"]).currency_id
            )
            to_curr = pricelist_uah.currency_id
            vals["pricelist_id"] = pricelist_uah.id

            for order_line in vals["order_line"]:
                line = order_line[2]
                line["price_unit"] = from_curr._convert(
                    line["price_unit"],
                    to_curr,
                    company_id,
                    fields.Datetime.to_datetime(
                        vals.get("date_order", fields.Datetime.now())
                    ),
                )

        return super().create(vals_list)
