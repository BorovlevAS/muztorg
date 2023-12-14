from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    afterpayment_check = fields.Boolean(
        string="Afterpayment check",
        inverse="_inverse_afterpayment_check",
        store=True,
        default=False,
    )
    backward_money_costs = fields.Float(
        "Amount to control payment (UAH)",
        compute="_compute_backward_money_costs",
        inverse="_inverse_backward_money_costs",
        store=True,
        readonly=False,
    )

    biko_ttn_ids = fields.One2many(
        comodel_name="delivery_novaposhta.ttn",
        inverse_name="order_to_deliver",
        string="TTN",
    )

    @api.depends("amount_total")
    def _compute_backward_money_costs(self):
        for order in self:
            cost = order.amount_total
            date = order.date_order or fields.Date.today()
            company = order.company_id.id or order.env.company.id
            currency_uah = order.env.ref("base.UAH").with_context(
                date=date, company_id=company
            )
            order_currency = order.currency_id
            if currency_uah != order_currency:
                cost = currency_uah.compute(cost, order_currency)
            order.backward_money_costs = cost

    def _inverse_afterpayment_check(self):
        for order in self:
            for stock in order.picking_ids:
                if stock.state != "done":
                    stock.update({"afterpayment_check": order.afterpayment_check})

    def _inverse_backward_money_costs(self):
        for order in self:
            for stock in order.picking_ids:
                if stock.state != "done":
                    stock.update({"backward_money_costs": order.backward_money_costs})

    # def _inverse_biko_ttn_ids(self):
    #     for order in self:
    #         for stock in order.picking_ids:
    #             if stock.state != "done":
    #                 stock.update({"backward_money_costs": order.backward_money_costs})
