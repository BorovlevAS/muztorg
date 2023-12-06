from odoo import models

from odoo.addons.base.models.res_bank import sanitize_account_number


class P24BBankSync(models.TransientModel):
    _inherit = "account.p24.sync"

    def _complete_stmts_vals(self, stmts_vals, journal, account_number):
        ResPB = self.env["res.partner.bank"]
        res_partner_model = self.env["res.partner"]
        for st_vals in stmts_vals:
            st_vals["journal_id"] = journal.id

            for line_vals in st_vals["transactions"]:
                unique_import_id = line_vals.get("unique_import_id")
                if unique_import_id:
                    sanitized_account_number = sanitize_account_number(account_number)
                    line_vals["unique_import_id"] = (
                        (
                            sanitized_account_number
                            and sanitized_account_number + "-"
                            or ""
                        )
                        + str(journal.id)
                        + "-"
                        + unique_import_id
                    )

                if not line_vals.get("bank_account_id"):
                    # Find the partner and his bank account or create
                    # the bank account. The partner selected during the
                    # reconciliation process will be linked to the bank
                    # when the statement is closed.
                    bank_account_id = False
                    identifying_string = False

                    if line_vals.get("partner_edrpou"):
                        partner_id = res_partner_model.search(
                            [
                                ("company_registry", "=", line_vals["partner_edrpou"]),
                                ("is_company", "=", True),
                            ],
                            limit=1,
                        )
                        if not partner_id and journal.is_create_partners:
                            partner_id = res_partner_model.create(
                                {
                                    "name": line_vals["partner_name"],
                                    "company_registry": line_vals["partner_edrpou"],
                                    "is_company": True,
                                }
                            )
                        line_vals.pop("partner_edrpou")
                        line_vals["partner_id"] = partner_id.id

                    if line_vals.get("partner_acc"):
                        identifying_string = line_vals.get("partner_acc")
                    else:
                        identifying_string = line_vals.get("account_number")
                    if identifying_string:
                        partner_bank = ResPB.search(
                            [("acc_number", "=", identifying_string)], limit=1
                        )
                        if partner_bank:
                            pass
                            # bank_account_id = partner_bank.id
                            # partner_id = partner_bank.partner_id.id
                        else:
                            if "partner_acc" in line_vals and line_vals["partner_acc"]:
                                if line_vals["partner_id"]:
                                    bank_account_id = ResPB.create(
                                        {
                                            "acc_number": line_vals["partner_acc"],
                                            "partner_id": line_vals["partner_id"],
                                        }
                                    ).id
                            else:
                                if line_vals["partner_id"]:
                                    bank_account_id = ResPB.create(
                                        {
                                            "acc_number": line_vals["account_number"],
                                            "partner_id": line_vals["partner_id"],
                                        }
                                    ).id

                    line_vals["bank_account_id"] = bank_account_id
                    if "partner_acc" in line_vals:
                        del line_vals["partner_acc"]

        return stmts_vals
