from odoo import fields, models


class SaleReport(models.Model):
    _inherit = "sale.report"

    margin = fields.Float(
        groups="muztorg_valuation_access_group.biko_group_show_margin"
    )
