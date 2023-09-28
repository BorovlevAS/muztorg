# Copyright 2015 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import base64
import os
import tempfile
from io import BytesIO

import babel
from docxtpl import DocxTemplate
from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError


def format_date(env, date, pattern=False, lang_code=False):
    try:
        return tools.format_date(env, date, date_format=pattern, lang_code=lang_code)
    except babel.core.UnknownLocaleError:
        return date


def format_datetime(env, dt, tz=False, dt_format="medium", lang_code=False):
    try:
        return tools.format_datetime(
            env, dt, tz=tz, dt_format=dt_format, lang_code=lang_code
        )
    except babel.core.UnknownLocaleError:
        return dt


class ReportDocxAbstract(models.AbstractModel):
    _name = "report.report_docx.abstract"
    _description = "Abstract DOCX Report"

    def _get_objs_for_report(self, docids, data):
        """
        Returns objects for xlx report.  From WebUI these
        are either as docids taken from context.active_ids or
        in the case of wizard are in data.  Manual calls may rely
        on regular context, setting docids, or setting data.

        :param docids: list of integers, typically provided by
            qwebactionmanager for regular Models.
        :param data: dictionary of data, if present typically provided
            by qwebactionmanager for TransientModels.
        :param ids: list of integers, provided by overrides.
        :return: recordset of active model for ids.
        """
        if docids:
            ids = docids
        elif data and "context" in data:
            ids = data["context"].get("active_ids", [])
        else:
            ids = self.env.context.get("active_ids", [])
        return self.env[self.env.context.get("active_model")].browse(ids)

    @api.model
    def create_docx_report(self, docids, data, report_template):
        objs = self._get_objs_for_report(docids, data)

        if report_template.datas:
            template_path = os.path.join(
                tempfile.gettempdir(), report_template.report_name + ".docx"
            )
            fdata = base64.b64decode(report_template.datas)
            with open(template_path, "wb") as f:
                f.write(fdata)
                f.close()
        else:
            raise UserError(
                _("{report_name} template was not found").format(
                    report_name=report_template.name
                )
            )

        context_leads = {
            "format_date": lambda date, date_format=False, lang_code=False: format_date(
                self.env, date, date_format, lang_code
            ),
            "format_datetime": lambda dt, tz=False, dt_format=False, lang_code=False: format_datetime(
                self.env, dt, tz, dt_format, lang_code
            ),
            "format_amount": lambda amount, currency, lang_code=False: tools.format_amount(
                self.env, amount, currency, lang_code
            ),
            "format_duration": lambda value: tools.format_duration(value),
            "user": self.env.user,
            "ctx": self._context,
        }
        context_leads["object"] = objs
        context_leads["current_date"] = context_leads["format_date"](
            fields.Date.context_today(objs)
        )

        # nom = 0
        # products = []
        # for str in objs.lead_product_ids:
        #     nom += 1
        #     products.append({
        #         'nom': nom,
        #         'product_id': str.product_id.with_context(lang='uk_UA').name,
        #         'qty': str.qty,
        #         'product_uom': str.product_uom.with_context(lang='uk_UA').name,
        #         'price_unit': str.price_unit,
        #         # 'biko_price_subtotal': str.biko_price_total,
        #     })

        # template_path = context_leads["path"]

        doc = DocxTemplate(template_path)

        doc.render(context_leads)

        # Удаление временных файлов
        os.remove(template_path)

        doc_buffer = BytesIO()
        doc.save(doc_buffer)
        doc_buffer.seek(0)

        # return doc_bytes
        return doc_buffer.read(), "docx"

    def generate_docx_report(self, workbook, data, objs):
        raise NotImplementedError()
