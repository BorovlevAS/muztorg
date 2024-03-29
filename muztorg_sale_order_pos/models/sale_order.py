from odoo import _, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    fiscal_receipt_req = fields.Selection(
        related="so_payment_type_id.fiscal_receipt_req",
        string="Fiscal Receipt Required (nnt)",
    )

    def action_open_receipt_wizard(self):
        self.ensure_one()
        view = self.env.ref(
            "checkbox_integration_sale_order.view_sale_order_checkbox_wizard_form"
        )

        create_values = {
            "order_id": self.id,
            "mobile_num": self.partner_id.mobile,
        }

        employee = self.env["hr.employee"].search(
            [("user_id", "=", self.env.user.id)], limit=1
        )

        if employee and employee.department_id:
            pos_config_ids = self.env["pos.config"].get_pos_config(
                employee.department_id.id
            )
            if pos_config_ids:
                create_values.update(
                    {
                        "config_id": pos_config_ids[0].id,
                        "pos_session_id": pos_config_ids[0].current_session_id.id,
                        "available_pos_config_ids": pos_config_ids._ids,
                    }
                )

        payment_types = self.env["so.payment.type"].search(
            [("fiscal_receipt_req", "in", ["yes", "after_receive"])]
        )

        new_lines = []
        for payment_type in payment_types:
            new_line = {
                "payment_type": payment_type.id,
                "payment_amount": self.amount_total
                if payment_type == self.so_payment_type_id
                else 0,
            }
            new_lines.append((0, 0, new_line))

        create_values.update({"payment_lines": new_lines})

        wizard = self.env["sale.order.checkbox.wizard"].create(create_values)

        action = {
            "name": _("Send Receipt to the Checkbox"),
            "type": "ir.actions.act_window",
            "res_model": "sale.order.checkbox.wizard",
            "view_mode": "form",
            "view_id": view.id,
            "target": "new",
            "res_id": wizard.id,
        }

        return action
