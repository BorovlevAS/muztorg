from odoo import fields, models
from odoo.tools.sql import column_exists, create_column


class StockPicking(models.Model):
    _inherit = "stock.picking"

    stock_request_order_id = fields.Many2one(
        related="group_id.stock_request_order_id",
        string="Stock Request Order",
        store=True,
        readonly=False,
    )

    def _auto_init(self):
        """
        Create related field here, too slow
        when computing it afterwards through _compute_related.

        Since group_id.sale_id is created in this module,
        no need for an UPDATE statement.
        """
        if not column_exists(self.env.cr, "stock_picking", "stock_request_order_id"):
            create_column(
                self.env.cr, "stock_picking", "stock_request_order_id", "int4"
            )
        return super()._auto_init()
