# Copyright 2018 Akretion (http://www.akretion.com)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# Copyright 2019 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def remove_ir_actions_report(cr, registry):
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        template_ids = env["biko.docx.template"].search([])
        for template in template_ids:
            report_action = env["ir.actions.report"].search(
                [("id", "=", template.report_action_id.id)]
            )
            report_action.unlink()
    _logger.warning(
        "The following View are modified and deleted with module uninstallation: %s"
        % template_ids.ids
    )
