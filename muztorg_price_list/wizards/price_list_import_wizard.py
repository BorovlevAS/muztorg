import base64
import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

logger = logging.getLogger(__name__)

try:
    pass

    import xlrd
    from xlrd.xldate import xldate_as_datetime
except (ImportError, OSError) as err:  # pragma: no cover
    logger.error(err)

try:
    pass
except ImportError:
    logger.warning(
        "chardet library not found, please install it "
        "from http://pypi.python.org/pypi/chardet"
    )


class PriceListImportWizard(models.TransientModel):
    _name = "price.list.import"
    _description = "Price List Import"

    price_file = fields.Binary(
        string="File",
        required=True,
    )
    price_filename = fields.Char()
    price_id = fields.Many2one("product.pricelist")

    def _import_file(self):
        self.ensure_one()
        result = {
            "price_ids": [],
            "notifications": [],
        }
        logger.info("Start to import Price List file %s", self.price_filename)
        file_data = base64.b64decode(self.price_file)
        self.import_single_file(file_data, result)
        logger.debug("result=%s", result)
        # if not result["price_ids"]:
        #     raise UserError(
        #         _(
        #             "You have already imported this file, or this file "
        #             "only contains already imported transactions."
        #         )
        #     )
        return result

    def import_file_button(self):
        """Process the file chosen in the wizard, create price list
        and return an action."""
        result = self._import_file()

        error_message = [
            message["message"]
            for message in result["notifications"]
            if message["type"] == "warning"
        ]

        if len(result["notifications"]) > 0:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Errors while downloading"),
                    "message": "\n".join(error_message),
                    "sticky": False,
                },
            }

        return {
            "type": "ir.actions.client",
            "tag": "reload",
        }

    def import_single_file(self, file_data, result):
        parsing_data = self.with_context(active_id=self.ids[0])._parse_file(file_data)
        logger.info(
            "Price list file %s contains %d lines",
            self.price_filename,
            len(parsing_data),
        )
        i = 0

        for single_line_data in parsing_data:
            i += 1
            logger.debug("line %d: single_line_data=%s", i, single_line_data)
            self.import_single_line(single_line_data, result, i)

    def import_single_line(self, single_line_data, result, ind_line):
        if not isinstance(single_line_data, dict):
            raise UserError(
                _("The parsing of the statement file returned an invalid result.")
            )

        price_ids = []
        notifications = []
        if single_line_data["control_code"] == "":
            notifications += [
                {
                    "type": "warning",
                    "message": _("The control code is not filled out in line No %s")
                    % ind_line,
                }
            ]

        product = self.env["product.template"].search(
            [("biko_control_code", "=", single_line_data["control_code"])]
        )
        if not product:
            notifications += [
                {
                    "type": "warning",
                    "message":
                    #     _("In line No. %s the Control code  %s is incorrect")
                    # % ind_line
                    # % single_line_data["control_code"],
                    _(
                        "In line No. %(line_number)s the Control code %(control_code)s is incorrect"
                    )
                    % {
                        "line_number": ind_line,
                        "control_code": single_line_data["control_code"],
                    },
                }
            ]
            result["notifications"].extend(notifications)
            return False

        price = self.price_id
        all_item = price.item_ids
        item_line = all_item.filtered(lambda x: x.product_tmpl_id.id == product.id)

        PricelistItem = self.env["product.pricelist.item"]

        if len(item_line) == 0:
            vals = {
                "applied_on": "1_product",
                "compute_price": "fixed",
                "pricelist_id": price.id,
                "base": "list_price",
            }
            vals["product_tmpl_id"] = product.id
            if single_line_data["date1"]:
                vals["date_start"] = single_line_data["date1"]
            if single_line_data["date2"]:
                vals["date_end"] = single_line_data["date2"]
            vals["fixed_price"] = single_line_data["price"]

            new_line = PricelistItem.create(vals)
            price_ids.append(new_line.id)
            is_download = True
        else:
            is_discont = single_line_data["date1"]
            is_download = False
            for line in item_line:
                if is_discont and not line.date_start:
                    continue
                if not is_discont and line.date_start:
                    continue
                # тут только нужная нам строка
                if not is_discont:
                    vals = {
                        "fixed_price": single_line_data["price"],
                    }
                    line.write(vals)
                    price_ids.append(line.id)
                    is_download = True
                    break
                elif single_line_data["date1"] < line.date_end:
                    vals = {
                        "applied_on": "1_product",
                        "compute_price": "fixed",
                        "pricelist_id": price.id,
                        "base": "list_price",
                    }
                    vals["product_tmpl_id"] = product.id
                    if single_line_data["date1"]:
                        vals["date_start"] = single_line_data["date1"]
                    if single_line_data["date2"]:
                        vals["date_end"] = single_line_data["date2"]
                    vals["fixed_price"] = single_line_data["price"]

                    new_line = PricelistItem.create(vals)
                    price_ids.append(new_line.id)
                    is_download = True
                else:
                    notifications += [
                        {
                            "type": "warning",
                            "message": _(
                                "The promotional price is already valid for the product %s."
                            )
                            % product.name,
                        }
                    ]
                    is_download = True
                    break
        if not is_download:
            vals = {
                "applied_on": "1_product",
                "compute_price": "fixed",
                "pricelist_id": price.id,
                "base": "list_price",
            }
            vals["product_tmpl_id"] = product.id
            if single_line_data["date1"]:
                vals["date_start"] = single_line_data["date1"]
            if single_line_data["date2"]:
                vals["date_end"] = single_line_data["date2"]
            vals["fixed_price"] = single_line_data["price"]

            new_line = PricelistItem.create(vals)
            price_ids.append(new_line.id)

        if notifications:
            result["notifications"].extend(notifications)

        if not price_ids:
            return False
        result["price_ids"].extend(price_ids)

    def _parse_file(self, data_file):
        self.ensure_one()
        try:
            Parser = self.env["biko.import.price.parser"]
            return Parser._parse_lines(data_file)

        except BaseException:
            logger.warning("Sheet parser error", exc_info=True)
            raise

        return 0


class AccountStatementImportSheetParser(models.TransientModel):
    _name = "biko.import.price.parser"
    _description = "Price List Import Sheet Parser"

    @api.model
    def parse(self, data_file, filename):
        # currency_code = price.currency_id.name
        lines = self._parse_lines(data_file)

        return lines

    def _get_column_names(self):
        return [
            "control_code_column",
            "name_column",
            "price_column",
            "date1_column",
            "date2_column",
        ]

    def _parse_lines(self, data_file):
        columns = dict()

        workbook = xlrd.open_workbook(
            file_contents=data_file,
            encoding_override=None,
        )
        csv_or_xlsx = (
            workbook,
            workbook.sheet_by_index(0),
        )

        column_index = 0
        for column_name in self._get_column_names():
            columns[column_name] = column_index
            column_index += 1
        return self._parse_rows(csv_or_xlsx, columns)

    def _get_values_from_column(self, values, columns, column_name):
        index = columns[column_name]
        content_l = []
        content_l.append(values[index])
        if all(isinstance(content, str) for content in content_l):
            return " ".join(content_l)
        return content_l[0]

    def _parse_row(self, values, columns):  # noqa: C901
        control_code = self._get_values_from_column(
            values, columns, "control_code_column"
        )
        name = self._get_values_from_column(values, columns, "name_column")
        date1 = self._get_values_from_column(values, columns, "date1_column")
        date2 = self._get_values_from_column(values, columns, "date2_column")

        price = self._get_values_from_column(values, columns, "price_column")

        line = {
            "control_code": control_code,
            "name": name,
            "date1": date1.date() if date1 != "" else False,
            "date2": date2.date() if date2 != "" else False,
            "price": price,
        }

        return line

    def _parse_rows(self, csv_or_xlsx, columns):  # noqa: C901
        rows = range(1, csv_or_xlsx[1].nrows)

        lines = []
        for row in rows:
            book = csv_or_xlsx[0]
            sheet = csv_or_xlsx[1]
            values = []
            for col_index in range(sheet.row_len(row)):
                cell_type = sheet.cell_type(row, col_index)
                cell_value = sheet.cell_value(row, col_index)
                if cell_type == xlrd.XL_CELL_DATE:
                    cell_value = xldate_as_datetime(cell_value, book.datemode)
                values.append(cell_value)
            line = self._parse_row(values, columns)
            if line:
                lines.append(line)
        return lines
