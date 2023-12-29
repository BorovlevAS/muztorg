from odoo import _, api, models
from odoo.osv import expression


class AccountReconciliation(models.AbstractModel):
    _inherit = "account.reconciliation.widget"

    @api.model
    def _get_statement_line(self, st_line):
        result = super()._get_statement_line(st_line)
        result.update({"payment_ref": st_line.payment_ref})

        return result

    @api.model
    def _prepare_move_lines(
        self, move_lines, target_currency=False, target_date=False, recs_count=0
    ):
        result = super()._prepare_move_lines(
            move_lines, target_currency, target_date, recs_count
        )

        for ret_line in result:
            move_line = self.env["account.move.line"].browse(ret_line["id"])
            field_data_list = move_line.move_id.invoice_line_ids.mapped(
                "sale_line_ids.order_id.biko_1c_ref"
            )
            field_data_list = [val for val in field_data_list if val]
            ret_line["biko_1c_ref"] = ",".join(field_data_list)

            field_data_list = move_line.move_id.invoice_line_ids.mapped(
                "sale_line_ids.order_id.biko_website_ref"
            )
            field_data_list = [val for val in field_data_list if val]
            ret_line["biko_website_ref"] = ",".join(field_data_list)

            field_data_list = move_line.move_id.invoice_line_ids.mapped(
                "sale_line_ids.order_id.so_payment_type_id.name"
            )
            field_data_list = [val for val in field_data_list if val]
            ret_line["so_payment_type_id"] = ",".join(field_data_list)

        return result

    def _str_domain_for_mv_line(self, search_str):
        result = super()._str_domain_for_mv_line(search_str)
        orders = self.env["sale.order"].search(
            [
                "|",
                ("biko_website_ref", "ilike", search_str),
                ("biko_1c_ref", "ilike", search_str),
            ]
        )
        if orders:
            move_ids = orders.mapped("invoice_ids")._ids
            result = expression.OR([result, [("move_id.id", "in", move_ids)]])

        return result

    @api.model
    # pylint: disable=dangerous-default-value
    def get_bank_statement_data(
        self,
        bank_statement_line_ids,
        srch_domain=[],  # noqa: B006
    ):
        """Get statement lines of the specified statements or all unreconciled
        statement lines and try to automatically reconcile them / find them
        a partner.
        Return ids of statement lines left to reconcile and other data for
        the reconciliation widget.

        :param bank_statement_line_ids: ids of the bank statement lines
        """
        if not bank_statement_line_ids:
            return {}
        domain = [
            ["id", "in", tuple(bank_statement_line_ids)],
            ("is_reconciled", "=", False),
            ("state", "=", "posted"),
        ] + srch_domain
        bank_statement_lines = self.env["account.bank.statement.line"].search(domain)
        bank_statements = bank_statement_lines.mapped("statement_id")

        results = self.get_bank_statement_line_data(bank_statement_lines.ids)
        bank_statement_lines_left = self.env["account.bank.statement.line"].browse(
            [line["st_line"]["id"] for line in results["lines"]]
        )
        bank_statements_left = bank_statement_lines_left.mapped("statement_id")

        results.update(
            {
                "statement_name": len(bank_statements_left) == 1
                and bank_statements_left.name
                or False,
                "journal_id": bank_statements
                and bank_statements[0].journal_id.id
                or False,
                "notifications": [],
            }
        )

        if len(results["lines"]) < len(bank_statement_lines):
            results["notifications"].append(
                {
                    "type": "info",
                    "template": "reconciliation.notification.reconciled",
                    "reconciled_aml_ids": results["reconciled_aml_ids"],
                    "nb_reconciled_lines": results["value_min"],
                    "details": {
                        "name": _("Journal Items"),
                        "model": "account.move.line",
                        "ids": results["reconciled_aml_ids"],
                    },
                }
            )

        return results
