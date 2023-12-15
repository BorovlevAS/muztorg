from odoo import fields, models


class AccountStatementImportSheetMapping(models.Model):
    _inherit = "account.statement.import.sheet.mapping"

    partner_ref_column = fields.Char(
        string="Partner reference column",
    )
