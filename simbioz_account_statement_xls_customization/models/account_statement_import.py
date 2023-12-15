import logging

from odoo import models

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
