from odoo import fields, models


class SaleOrderCheckbox(models.TransientModel):
    _inherit = "sale.order.checkbox.wizard"

    # TODO: make this field computed
    available_pos_config_ids = fields.Many2many(
        comodel_name="pos.config",
        string="Available POS (nnt)",
    )

    config_id = fields.Many2one(domain="[('id', 'in', available_pos_config_ids)]")
    pos_session_id = fields.Many2one(required=False)
    payment_lines = fields.One2many(
        comodel_name="sale.order.checkbox.wizard.line",
        inverse_name="wizard_id",
        string="Payments",
    )


class SaleOrderCheckboxWizardLine(models.TransientModel):
    _name = "sale.order.checkbox.wizard.line"
    _description = "Sale Order Checkbox Wizard Line (nnt)"

    wizard_id = fields.Many2one(
        comodel_name="sale.order.checkbox.wizard", string="Wizard"
    )

    payment_type = fields.Many2one(
        comodel_name="so.payment.type",
        string="Payment Type",
        required=True,
    )

    payment_amount = fields.Float(string="Payment Amount", required=True)
