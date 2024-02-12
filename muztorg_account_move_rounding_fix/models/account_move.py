from odoo import _, models
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    def _check_balanced(self):
        """Assert the move is fully balanced debit = credit.
        An error is raised if it's not the case.
        """
        moves = self.filtered(lambda move: move.line_ids)
        if not moves:
            return

        # /!\ As this method is called in create / write, we can't make the assumption the computed stored fields
        # are already done. Then, this query MUST NOT depend of computed stored fields (e.g. balance).
        # It happens as the ORM makes the create with the 'no_recompute' statement.
        self.env["account.move.line"].flush(self.env["account.move.line"]._fields)
        self.env["account.move"].flush(["journal_id"])
        self._cr.execute(
            """
            SELECT line.move_id, ROUND(SUM(line.debit - line.credit), currency.decimal_places)
            FROM account_move_line line
            JOIN account_move move ON move.id = line.move_id
            JOIN account_journal journal ON journal.id = move.journal_id
            JOIN res_company company ON company.id = journal.company_id
            JOIN res_currency currency ON currency.id = company.currency_id
            WHERE line.move_id IN %s
            GROUP BY line.move_id, currency.decimal_places
            HAVING ROUND(SUM(line.debit - line.credit), currency.decimal_places) != 0.0;
        """,
            [tuple(self.ids)],
        )

        query_res = self._cr.fetchall()
        for move_id, diff in query_res:
            if abs(diff) > self.env.company.max_avail_diff:
                move = self.browse(move_id)
                raise UserError(
                    _(
                        "Cannot create unbalanced journal entry. Id: %()s\nDifferences debit - credit: %()s",
                        move.id,
                        diff,
                    )
                )
            move = self.browse(move_id)
            line = {
                "move_id": move_id,
                "name": _("Difference"),
                "account_id": (
                    move.company_id.revaluation_loss_account_id.id
                    if diff < 0
                    else move.company_id.revaluation_gain_account_id.id
                ),
                "debit": diff < 0 and -diff or 0,
                "credit": diff > 0 and diff or 0,
            }
            self.env["account.move.line"].create(line)

        # if query_res:
        #     ids = [res[0] for res in query_res]
        #     sums = [res[1] for res in query_res]
        #     raise UserError(_("Cannot create unbalanced journal entry. Ids: %s\nDifferences debit - credit: %s") % (ids, sums))
