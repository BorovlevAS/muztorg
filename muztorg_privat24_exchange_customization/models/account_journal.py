from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    is_create_partners = fields.Boolean(
        string="Create Partners",
        help="Automatically create a partner if not found during import",
    )
