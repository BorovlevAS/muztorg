import functools
import logging

import odoo
import psycopg2
from odoo import _, api, models
from odoo.tools.lru import LRU
from odoo.tools.misc import CountingStream

from .ir_fields import REFERENCING_FIELDS

_logger = logging.getLogger(__name__)


class BaseModel(models.AbstractModel):
    _inherit = "base"

    def _add_fake_fields(self, fields):
        from odoo.fields import Char

        result = super()._add_fake_fields(fields=fields)
        result[".biko_control_code"] = Char("Control code")
        return result

    @api.model
    def _convert_records(self, records, log=lambda a: None):
        """Converts records from the source iterable (recursive dicts of
        strings) into forms which can be written to the database (via
        self.create or (ir.model.data)._update)

        :returns: a list of triplets of (id, xid, record)
        :rtype: list((int|None, str|None, dict))
        """
        field_names = {name: field.string for name, field in self._fields.items()}
        if self.env.lang:
            field_names.update(self.env["ir.translation"].get_field_string(self._name))

        convert = self.env["ir.fields.converter"].for_model(self)

        def _log(base, record, field, exception):
            type = "warning" if isinstance(exception, Warning) else "error"
            # logs the logical (not human-readable) field name for automated
            # processing of response, but injects human readable in message
            exc_vals = dict(base, record=record, field=field_names[field])
            record = dict(
                base,
                type=type,
                record=record,
                field=field,
                message=str(exception.args[0]) % exc_vals,
            )
            if len(exception.args) > 1 and isinstance(exception.args[1], dict):
                record.update(exception.args[1])
            log(record)

        stream = CountingStream(records)
        for record, extras in stream:
            # xid
            xid = record.get("id", False)
            # dbid
            dbid = False
            if ".id" in record:
                try:
                    dbid = int(record[".id"])
                except ValueError:
                    # in case of overridden id column
                    dbid = record[".id"]
                if not self.search([("id", "=", dbid)]):
                    log(
                        dict(
                            extras,
                            type="error",
                            record=stream.index,
                            field=".id",
                            message=_("Unknown database identifier '%s'", dbid),
                        )
                    )
                    dbid = False
            elif "biko_control_code" in record:
                search_value = record["biko_control_code"]
                ids = self.search([("biko_control_code", "=", search_value)])

                if ids:
                    if len(ids) > 1:
                        log(
                            dict(
                                extras,
                                type="error",
                                record=stream.index,
                                field="biko_control_code",
                                message=_(
                                    "Found multiple matches for control code '%s' (%d matches)"
                                )
                                % (search_value, len(ids)),
                            )
                        )
                        dbid = False
                    else:
                        dbid = ids[0].id

            converted = convert(record, functools.partial(_log, extras, stream.index))

            yield dbid, xid, converted, dict(extras, record=stream.index)

    @api.model
    def load(self, fields, data):
        """
        Attempts to load the data matrix, and returns a list of ids (or
        ``False`` if there was an error and no id could be generated) and a
        list of messages.

        The ids are those of the records created and saved (in database), in
        the same order they were extracted from the file. They can be passed
        directly to :meth:`~read`

        :param fields: list of fields to import, at the same index as the corresponding data
        :type fields: list(str)
        :param data: row-major matrix of data to import
        :type data: list(list(str))
        :returns: {ids: list(int)|False, messages: [Message][, lastrow: int]}
        """
        self.flush()

        # determine values of mode, current_module and noupdate
        mode = self._context.get("mode", "init")
        current_module = self._context.get("module", "__import__")
        noupdate = self._context.get("noupdate", False)
        # add current module in context for the conversion of xml ids
        self = self.with_context(_import_current_module=current_module)

        cr = self._cr
        cr.execute("SAVEPOINT model_load")

        fields = [models.fix_import_export_id_paths(f) for f in fields]
        fg = self.fields_get()

        ids = []
        messages = []

        # list of (xid, vals, info) for records to be created in batch
        batch = []
        batch_xml_ids = set()
        # models in which we may have created / modified data, therefore might
        # require flushing in order to name_search: the root model and any
        # o2m
        creatable_models = {self._name}
        for field_path in fields:
            if field_path[0] in REFERENCING_FIELDS:
                continue
            model_fields = self._fields
            if isinstance(model_fields[field_path[0]], odoo.fields.Many2one):
                # this only applies for toplevel m2o (?) fields
                if field_path[0] in (
                    self.env.context.get("name_create_enabled_fieds") or {}
                ):
                    creatable_models.add(model_fields[field_path[0]].comodel_name)
            for field_name in field_path:
                if field_name in REFERENCING_FIELDS:
                    break

                if isinstance(model_fields[field_name], odoo.fields.One2many):
                    comodel = model_fields[field_name].comodel_name
                    creatable_models.add(comodel)
                    model_fields = self.env[comodel]._fields

        def flush(*, xml_id=None, model=None):
            if not batch:
                return

            assert not (
                xml_id and model
            ), "flush can specify *either* an external id or a model, not both"

            if xml_id and xml_id not in batch_xml_ids:
                if xml_id not in self.env:
                    return
            if model and model not in creatable_models:
                return

            data_list = [
                dict(xml_id=xid, values=vals, info=info, noupdate=noupdate)
                for xid, vals, info in batch
            ]
            batch.clear()
            batch_xml_ids.clear()

            # try to create in batch
            try:
                with cr.savepoint():
                    recs = self._load_records(data_list, mode == "update")
                    ids.extend(recs.ids)
                return
            except psycopg2.InternalError as e:
                # broken transaction, exit and hope the source error was already logged
                if not any(message["type"] == "error" for message in messages):
                    info = data_list[0]["info"]
                    messages.append(
                        dict(
                            info,
                            type="error",
                            message=_("Unknown database error: '%s'", e),
                        )
                    )
                return
            except Exception:
                pass

            errors = 0
            # try again, this time record by record
            for i, rec_data in enumerate(data_list, 1):
                try:
                    with cr.savepoint():
                        rec = self._load_records([rec_data], mode == "update")
                        ids.append(rec.id)
                except psycopg2.Warning as e:
                    info = rec_data["info"]
                    messages.append(dict(info, type="warning", message=str(e)))
                except psycopg2.Error as e:
                    info = rec_data["info"]
                    messages.append(
                        dict(
                            info,
                            type="error",
                            **models.PGERROR_TO_OE[e.pgcode](self, fg, info, e)
                        )
                    )
                    # Failed to write, log to messages, rollback savepoint (to
                    # avoid broken transaction) and keep going
                    errors += 1
                except Exception as e:
                    _logger.debug("Error while loading record", exc_info=True)
                    info = rec_data["info"]
                    message = _("Unknown error during import:") + " %s: %s" % (
                        type(e),
                        e,
                    )
                    moreinfo = _("Resolve other errors first")
                    messages.append(
                        dict(info, type="error", message=message, moreinfo=moreinfo)
                    )
                    # Failed for some reason, perhaps due to invalid data supplied,
                    # rollback savepoint and keep going
                    errors += 1
                if errors >= 10 and (errors >= i / 10):
                    messages.append(
                        {
                            "type": "warning",
                            "message": _(
                                "Found more than 10 errors and more than one error per 10 records, interrupted to avoid showing too many errors."
                            ),
                        }
                    )
                    break

        # make 'flush' available to the methods below, in the case where XMLID
        # resolution fails, for instance
        flush_self = self.with_context(import_flush=flush, import_cache=LRU(1024))

        # TODO: break load's API instead of smuggling via context?
        limit = self._context.get("_import_limit")
        if limit is None:
            limit = float("inf")
        extracted = flush_self._extract_records(
            fields, data, log=messages.append, limit=limit
        )

        converted = flush_self._convert_records(extracted, log=messages.append)

        info = {"rows": {"to": -1}}
        for id, xid, record, info in converted:
            if xid:
                xid = xid if "." in xid else "%s.%s" % (current_module, xid)
                batch_xml_ids.add(xid)
            elif id:
                record["id"] = id
            batch.append((xid, record, info))

        flush()
        if any(message["type"] == "error" for message in messages):
            cr.execute("ROLLBACK TO SAVEPOINT model_load")
            ids = False
            # cancel all changes done to the registry/ormcache
            self.pool.reset_changes()

        nextrow = info["rows"]["to"] + 1
        if nextrow < limit:
            nextrow = 0
        return {
            "ids": ids,
            "messages": messages,
            "nextrow": nextrow,
        }
