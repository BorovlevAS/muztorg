import logging

from odoo import _, api, models
from odoo.exceptions import UserError

from odoo.addons.base.models.res_bank import sanitize_account_number

_logger = logging.getLogger(__name__)


class AccountStatementImport(models.TransientModel):
    """Add process_camt method to account.bank.statement.import."""

    _inherit = "account.statement.import"

    def _complete_stmts_vals(self, stmts_vals, journal, account_number):
        """Search partner from partner reference"""
        stmts_vals = super()._complete_stmts_vals(stmts_vals, journal, account_number)
        for st_vals in stmts_vals:
            for line_vals in st_vals["transactions"]:
                if "partner_ref" in line_vals:
                    partner_ref = line_vals.pop("partner_ref")
                    partner_id = self.env["res.partner"].search(
                        [("enterprise_code", "=", partner_ref)], limit=1
                    )
                    if partner_id:
                        line_vals["partner_id"] = partner_id.id

        return stmts_vals

    @api.model
    def _match_journal(self, account_number, currency):
        company = self.env.company
        journal_obj = self.env["account.journal"]
        if not account_number:  # exemple : QIF
            if not self.env.context.get("journal_id"):
                raise UserError(
                    _(
                        "The format of this bank statement file doesn't "
                        "contain the bank account number, so you must "
                        "start the wizard from the right bank journal "
                        "in the dashboard."
                    )
                )
            journal = journal_obj.browse(self.env.context.get("journal_id"))
        else:
            sanitized_account_number = sanitize_account_number(account_number)

            journal = journal_obj.search(
                [
                    ("type", "=", "bank"),
                    (
                        "bank_account_id.sanitized_acc_number",
                        "ilike",
                        sanitized_account_number,
                    ),
                ],
                limit=1,
            )
            journal_id = self.env.context.get("journal_id")
            if journal_id and journal.id != journal_id:
                # For accounts with the same number but different currencies
                # Для счетов с одним номером, но разной валютой
                journal = journal_obj.search(
                    [
                        ("type", "=", "bank"),
                        (
                            "bank_account_id.sanitized_acc_number",
                            "ilike",
                            sanitized_account_number,
                        ),
                        (
                            "currency_id",
                            "=",
                            journal_obj.browse(
                                self.env.context.get("journal_id")
                            ).currency_id.id,
                        ),
                    ],
                    limit=1,
                )
                if journal.id != journal_id:
                    raise UserError(
                        _(
                            "The journal found for the file is not consistent with the "
                            "selected journal. You should use the proper journal or "
                            "use the generic button on the top of the Accounting Dashboard"
                        )
                    )

            if not journal:
                bank_accounts = self.env["res.partner.bank"].search(
                    [
                        ("partner_id", "=", company.partner_id.id),
                        ("sanitized_acc_number", "ilike", sanitized_account_number),
                    ],
                    limit=1,
                )
                if bank_accounts:
                    raise UserError(
                        _(
                            "The bank account with number '{}' exists in Odoo "
                            "but it is not set on any bank journal. You should "
                            "set it on the related bank journal. If the related "
                            "bank journal doesn't exist yet, you should create "
                            "a new one."
                        ).format(account_number)
                    )
                else:
                    raise UserError(
                        _(
                            "Could not find any bank account with number '{account_number}' "
                            "linked to partner '{partner_name}'. You should create the bank "
                            "account and set it on the related bank journal. "
                            "If the related bank journal doesn't exist yet, you "
                            "should create a new one."
                        ).format(
                            account_number=account_number,
                            partner_name=company.partner_id.display_name,
                        )
                    )

        # We support multi-file and multi-statement in a file
        # so self.env.context.get('journal_id') doesn't mean much
        # I don't think we should really use it
        journal_currency = journal.currency_id or company.currency_id
        if journal_currency != currency:
            raise UserError(
                _(
                    "The currency of the bank statement ({currency}) is not the same as the "
                    "currency of the journal '{journal}' ({journal_currency})."
                ).format(
                    currency=currency.name,
                    journal=journal.display_name,
                    journal_currency=journal_currency.name,
                )
            )
        return journal
