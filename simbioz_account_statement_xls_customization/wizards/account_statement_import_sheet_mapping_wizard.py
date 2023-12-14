# Copyright 2019 ForgeFlow, S.L.
# Copyright 2020 CorporateHub (https://corporatehub.eu)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


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
