from odoo import fields, models


class AccountBankStatement(models.Model):
    _inherit = "account.bank.statement"

    def button_post(self):
        result = super().button_post()
        for statement in self.filtered(
            lambda x: x.pos_session_id and x.state == "posted"
        ):
            for line in statement.line_ids.filtered(lambda x: x.pos_payment_id):
                move_line_ids = line.pos_payment_id.line_ids.filtered(
                    lambda x, line=line: x.account_id
                    == line.pos_payment_id.journal_id.payment_debit_account_id
                )
                for move_line in move_line_ids:
                    line.reconcile([{"id": move_line.id}])
        return result


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    pos_payment_id = fields.Many2one(
        comodel_name="account.payment",
        string="POS Payment (nnt)",
        copy=False,
    )
