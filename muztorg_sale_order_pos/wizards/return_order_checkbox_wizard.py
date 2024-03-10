import base64
import logging
import time

import requests

from odoo import _, api, fields, models, tools
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

CHECKBOX_TAX_TABLE = {
    0: 8,
    7: 4,
    20: 1,
}


class ReturnOrderCheckbox(models.TransientModel):
    _name = "return.order.checkbox.wizard"
    _inherit = ["phone.validation.mixin"]
    _description = "Return Order Checkbox Wizard"

    order_id = fields.Many2one(
        comodel_name="sale.stock.return", string="Order", readonly=True, required=True
    )

    available_pos_config_ids = fields.Many2many(
        comodel_name="pos.config",
        string="Available POS (nnt)",
    )

    config_id = fields.Many2one(
        comodel_name="pos.config",
        domain="[('id', 'in', available_pos_config_ids)]",
        string="POS",
        required=True,
    )

    currency_id = fields.Many2one(
        comodel_name="res.currency",
        related="order_id.currency_id",
        string="Currency (nnt)",
    )
    order_amount_total = fields.Monetary(
        related="order_id.amount_total",
        string="Order Amount Total",
    )

    pos_session_id = fields.Many2one(
        comodel_name="pos.session",
        string="Session",
        related="config_id.current_session_id",
        required=False,
    )
    payment_lines = fields.One2many(
        comodel_name="return.order.checkbox.wizard.line",
        inverse_name="wizard_id",
        string="Payments",
    )
    mobile_num = fields.Char(string="Mobile Number")

    @api.onchange("mobile_num")
    def _onchange_phone_validation(self):
        if self.mobile_num:
            self.mobile_num = self.phone_format(
                number=self.mobile_num, force_format="E164"
            )
            if self.mobile_num[0] == "+":
                self.mobile_num = self.mobile_num[1:]

    def _register_fiscal_receipt(self):
        payload = {
            "goods": [],
            "payments": [],
            "related_receipt_id": self.order_id.sale_order_id.checkbox_receipt_id,
            "delivery": {"phone": self.mobile_num},
        }
        so_payment_vals = []

        for line in self.order_id.line_ids:
            good_value = {
                "good": {
                    "code": line.product_id.id,
                    "name": line.product_id.name,
                    "price": round(line.price_unit * 100, 2),
                    "barcode": line.product_id.barcode,
                    "tax": [],
                },
                "quantity": round(line.quantity_return * 1000, 2),
                "is_return": "true",
            }
            if line.tax_id:
                for tax in line.tax_id:
                    good_value["good"]["tax"].append(CHECKBOX_TAX_TABLE[tax.amount])
            else:
                good_value["good"]["tax"].append(8)

            if line.discount:
                good_value.update(
                    {
                        "discounts": [
                            {
                                "type": "DISCOUNT",
                                "mode": "PERCENT",
                                "value": line.discount,
                            }
                        ]
                    }
                )

            payload["goods"].append(good_value)

        for payment in self.payment_lines:
            if payment.payment_amount == 0:
                continue
            payment_vals = {
                "type": (
                    payment.payment_type.checkbox_payment_type
                    if payment.payment_type.checkbox_payment_type
                    else "CASH"
                ),
                "value": round(payment.payment_amount * 100, 2),
            }
            if payment.payment_type.checkbox_payment_label:
                payment_vals.update(
                    {"label": payment.payment_type.checkbox_payment_label}
                )
            payload["payments"].append(payment_vals)
            so_payment_vals.append(
                (
                    0,
                    0,
                    {
                        "payment_type": payment.payment_type.id,
                        "pos_payment_method_id": payment.pos_payment_method_id.id,
                        "payment_amount": payment.payment_amount,
                    },
                )
            )

        response = requests.post(
            self.config_id.checkbox_url + "/api/v1/receipts/sell",
            headers={
                "Accept": "application/json;",
                "Authorization": "Bearer " + self.pos_session_id.checkbox_access_token,
            },
            json=payload,
            timeout=5,
        )
        if not response.ok:
            raise ValidationError(response.text)

        data = response.json()
        self.order_id.update(
            {
                "checkbox_receipt_id": data["id"],
                "checkbox_receipt_response": str(data),
                "pos_session_id": self.pos_session_id.id,
                "return_order_pos_line_ids": so_payment_vals,
            }
        )

        self._checkbox_get_pdf_receipt()

    def _checkbox_get_pdf_receipt(self):
        self.ensure_one()
        if self.order_id.checkbox_receipt_id:
            time.sleep(10)
            headers = {
                "Authorization": "Bearer %s"
                % self.pos_session_id.checkbox_access_token,
            }

            response_qrcode = requests.get(
                "%s/api/v1/receipts/%s/qrcode"
                % (self.config_id.checkbox_url, self.order_id.checkbox_receipt_id),
                headers=headers,
                timeout=5,
            )
            if response_qrcode.ok:
                self.order_id.checkbox_receipt_qr_code = base64.b64encode(
                    response_qrcode.content
                )

            response_html = requests.get(
                "%s/api/v1/receipts/%s/html"
                % (self.config_id.checkbox_url, self.order_id.checkbox_receipt_id),
                headers=headers,
                timeout=5,
            )
            if response_html.ok:
                self.order_id.checkbox_receipt_html = response_html.content.decode()

            response_pdf = requests.get(
                "%s/api/v1/receipts/%s/pdf"
                % (self.config_id.checkbox_url, self.order_id.checkbox_receipt_id),
                headers=headers,
                timeout=5,
            )
            if not response_pdf.ok:
                _logger.warning(
                    "Error _checkbox_get_pdf_receipt: %s", response_pdf.text
                )

    def send_receipt_checkbox(self):
        self.ensure_one()
        self.check_settings()
        self.create_payment()
        self._register_fiscal_receipt()

    def check_settings(self):
        amount_total = tools.float_round(
            sum(self.payment_lines.mapped("payment_amount")),
            precision_rounding=self.currency_id.rounding,
        )
        if (
            tools.float_compare(
                amount_total,
                self.order_id.amount_total,
                precision_rounding=self.currency_id.rounding,
            )
            != 0
        ):
            raise ValidationError(
                _("The amount of payments does not match the amount of the order")
            )

        if any(
            self.payment_lines.filtered(
                lambda x: x.payment_amount > 0 and not x.pos_payment_method_id
            )
        ):
            raise ValidationError(
                _(
                    "There is no payment method for the selected payment type. Please, contact the administrator."
                )
            )

    def create_payment(self):
        invoice_id = self.order_id.account_move_ids.filtered(
            lambda x: x.state == "posted" and x.payment_state == "not_paid"
        )
        if not invoice_id:
            raise ValidationError(_("There is no invoice to pay"))

        if len(invoice_id) > 1:
            invoice_id = invoice_id[0]

        for payment_line in self.payment_lines.filtered(lambda x: x.payment_amount > 0):
            create_vals = {
                "journal_id": payment_line.pos_payment_method_id.cash_journal_id.id,
                "amount": payment_line.payment_amount,
            }
            wizard = (
                self.env["account.payment.register"]
                .with_context(
                    active_model="account.move",
                    active_ids=invoice_id.ids,
                )
                .create(create_vals)
            )
            payment_id = wizard._create_payments()

            if not payment_line.pos_payment_method_id.is_cash_count:
                continue
            # ищем кассовую выписку, куда нужно добавить эту сумму
            bank_statement_id = self.pos_session_id.statement_ids.filtered(
                lambda x, payment_line=payment_line: x.journal_id
                == payment_line.pos_payment_method_id.cash_journal_id
            )
            if not bank_statement_id:
                raise ValidationError(
                    _("There is no cash statement to add this amount")
                )
            if len(bank_statement_id) > 1:
                bank_statement_id = bank_statement_id[0]
            absl_values = {
                "statement_id": bank_statement_id.id,
                "date": bank_statement_id.date,
                "payment_type": "purchase",
                "payment_subtype": "2",
                "payment_ref": invoice_id.name,
                "partner_id": self.order_id.partner_id.id,
                "contract_id": (
                    self.order_id.contract_id.id if self.order_id.contract_id else False
                ),
                "sale_order_id": self.order_id.sale_order_id.id,
                "amount": -payment_line.payment_amount,
                "account_id": payment_line.pos_payment_method_id.cash_journal_id.suspense_account_id.id,
                "pos_payment_id": payment_id.id,
            }
            self.env["account.bank.statement.line"].create(absl_values)

    @api.model_create_multi
    def create(self, vals):
        for val in vals:
            if val.get("mobile_num"):
                val["mobile_num"] = self.phone_format(
                    number=val["mobile_num"], force_format="E164"
                )
                if val["mobile_num"][0] == "+":
                    val["mobile_num"] = val["mobile_num"][1:]
        return super().create(vals)


class ReturnOrderCheckboxWizardLine(models.TransientModel):
    _name = "return.order.checkbox.wizard.line"
    _description = "Return Order Checkbox Wizard Line (nnt)"

    wizard_id = fields.Many2one(
        comodel_name="return.order.checkbox.wizard", string="Wizard"
    )
    pos_config_id = fields.Many2one(
        comodel_name="pos.config",
        related="wizard_id.config_id",
        string="POS Config (nnt)",
    )

    payment_type = fields.Many2one(
        comodel_name="so.payment.type",
        string="Payment Type",
        required=True,
    )

    pos_payment_method_id = fields.Many2one(
        comodel_name="pos.payment.method",
        compute="_compute_pos_pm",
        string="Payment Method (nnt)",
        store=True,
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        related="wizard_id.currency_id",
        string="Currency (nnt)",
    )
    payment_amount = fields.Monetary(string="Payment Amount", required=True)

    @api.depends("payment_type", "pos_config_id")
    def _compute_pos_pm(self):
        for rec in self:
            rec.pos_payment_method_id = (
                self.env["sale.pos.payment.line"]
                .search(
                    [
                        ("pos_config_id", "=", rec.pos_config_id.id),
                        ("sale_order_payment_id", "=", rec.payment_type.id),
                    ]
                )
                .pos_payment_method_id
            )
