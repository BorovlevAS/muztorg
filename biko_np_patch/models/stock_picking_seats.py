from odoo import api, fields, models


class NovaPoshtaSeats(models.Model):
    _name = "novaposhta.seats"
    _description = "Nova poshta seats"

    # name = fields.Char()
    stock_picking_id = fields.Many2one(comodel_name="stock.picking", ondelete="cascade")
    np_shipping_weight = fields.Float(string="Shipping Weight")
    np_shipping_volume = fields.Float(string="Shipping Volume", digits=(10, 4))
    np_length = fields.Integer(
        string="Length (cm)",
        help="The cargo length (cm)",
    )
    np_width = fields.Integer(
        string="Width (cm)",
        help="The cargo width (cm)",
    )
    np_height = fields.Integer(
        string="Height (cm)",
        help="The cargo height (cm)",
    )
    biko_volume_weight = fields.Float(string="Volume Weight", digits=(10, 4))

    @api.onchange("np_length", "np_width", "np_height")
    def _on_change_dimensions(self):
        for rec in self:
            rec.np_shipping_volume = (
                rec.np_length * rec.np_width * rec.np_height
            ) / 1_000_000
            rec.biko_volume_weight = (
                rec.np_length * rec.np_width * rec.np_height
            ) / 4_000
