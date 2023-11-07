from odoo import fields, models

# from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    afterpayment_check = fields.Boolean(string="Afterpayment check", default=False)
    backward_money_costs = fields.Float(
        "Amount to control payment (UAH)",
        compute="_compute_backward_money_costs",
    )

    def _compute_backward_money_costs(self):
        cost = self.amount_total
        date = self.date_order or fields.Date.today()
        company = self.company_id.id or self.env.company.id
        currency_uah = self.env.ref("base.UAH").with_context(
            date=date, company_id=company
        )
        order_currency = self.currency_id
        if currency_uah != order_currency:
            cost = currency_uah.compute(cost, order_currency)
        self.backward_money_costs = cost
