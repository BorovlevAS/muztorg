from odoo import fields, models


class AccountStatementImportSheetMappingWizardHotkey(models.TransientModel):
    _inherit = "account.statement.import.sheet.mapping.wizard"

    partner_ref_column = fields.Char(
        string="Partner Reference column",
    )

    def _get_mapping_values(self):
        res = super()._get_mapping_values()
        res["partner_ref_column"] = self.partner_ref_column
        return res
