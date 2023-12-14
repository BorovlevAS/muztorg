import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class AccountStatementImportSheetParser(models.TransientModel):
    _inherit = "account.statement.import.sheet.parser"

    def _get_column_names(self):
        return super()._get_column_names() + ["partner_ref_column"]

    def _parse_row(self, mapping, currency_code, values, columns):  # noqa: C901
        line = super()._parse_row(mapping, currency_code, values, columns)
        partner_ref = (
            self._get_values_from_column(values, columns, "partner_ref_column")
            if columns["partner_ref_column"]
            else None
        )
        if partner_ref is not None:
            line["partner_ref"] = partner_ref
        return line

    @api.model
    def _convert_line_to_transactions(self, line):  # noqa: C901
        transaction = super()._convert_line_to_transactions(line)
        partner_ref = line.get("partner_ref")
        if partner_ref:
            transaction[0]["partner_ref"] = partner_ref

        return transaction
