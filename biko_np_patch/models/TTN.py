from odoo import models


class NovaPoshtaTTN(models.Model):
    _inherit = "delivery_novaposhta.ttn"

    def _data_from_sale_order(self):
        """Получение данных с заказа продаж, что б ручкамине заполнять"""

        for record in self:
            # product data
            if not self._context.get("autocreate"):
                record.seats_amount = record.order_to_deliver.seats_amount
                address = record.order_to_deliver.partner_shipping_id
                if address:
                    record.recipient_city = address.np_city
                    record.streets = address.np_city
            delivery_np = self.env.ref("novaposhta_data.product_product_delivery_np")
            order_line = record.order_to_deliver.order_line.filtered(
                lambda ol, delivery_np=delivery_np: ol.product_id != delivery_np
            )
            if record.cost == 0:
                cost = sum([ol.price_total for ol in order_line])
                currency_uah = self.env.ref("base.UAH")
                order_currency = record.order_to_deliver.currency_id
                if currency_uah != order_currency:
                    cost = currency_uah.compute(cost, order_currency)
                record.cost = cost
            if record.seats_amount > 0:
                record.weight = (
                    sum(
                        [
                            (line.product_id.weight * line.product_uom_qty)
                            for line in order_line
                        ]
                    )
                    or 0.0
                )
                record.general_volume = (
                    sum(
                        [
                            (line.product_id.volume * line.product_uom_qty)
                            for line in order_line
                        ]
                    )
                    or 0.0
                )
            # recipient data
            record.recipient_type = record.order_to_deliver.partner_id.np_type
            if record.order_to_deliver.partner_id.np_type.ref == "Organization":
                record.recipient_name_organization = record.order_to_deliver.partner_id
                record.recipient_name = record.order_to_deliver.biko_recipient_id
            else:
                record.recipient_name = record.order_to_deliver.partner_id
            # salesperson
            record.salesperson = record.order_to_deliver.user_id
