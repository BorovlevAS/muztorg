import psycopg2
from odoo import _, api, models
from odoo.addons.base.models.ir_fields import REFERENCING_FIELDS, ImportWarning

REFERENCING_FIELDS.update({".biko_control_code"})


class IrFieldsConverter(models.AbstractModel):
    _inherit = "ir.fields.converter"

    @api.model
    def db_id_for(self, model, field, subfield, value):
        """Finds a database id for the reference ``value`` in the referencing
        subfield ``subfield`` of the provided field of the provided model.

        :param model: model to which the field belongs
        :param field: relational field for which references are provided
        :param subfield: a relational subfield allowing building of refs to
                         existing records: ``None`` for a name_get/name_search,
                         ``id`` for an external id and ``.id`` for a database
                         id
        :param value: value of the reference to match to an actual record
        :param context: OpenERP request context
        :return: a pair of the matched database identifier (if any), the
                 translated user-readable name for the field and the list of
                 warnings
        :rtype: (ID|None, unicode, list)
        """
        # the function 'flush' comes from BaseModel.load(), and forces the
        # creation/update of former records (batch creation)
        flush = self._context.get("import_flush", lambda **kw: None)

        id = None
        warnings = []
        error_msg = ""
        action = {
            "name": "Possible Values",
            "type": "ir.actions.act_window",
            "target": "new",
            "view_mode": "tree,form",
            "views": [(False, "list"), (False, "form")],
            "context": {"create": False},
            "help": _("See all possible values"),
        }
        if subfield is None:
            action["res_model"] = field.comodel_name
        elif subfield in ("id", ".id"):
            action["res_model"] = "ir.model.data"
            action["domain"] = [("model", "=", field.comodel_name)]

        RelatedModel = self.env[field.comodel_name]
        if subfield == ".id":
            field_type = _("database id")
            if (
                isinstance(value, str)
                and not self._str_to_boolean(model, field, value)[0]
            ):
                return False, field_type, warnings
            try:
                tentative_id = int(value)
            except ValueError:
                tentative_id = value
            try:
                if RelatedModel.search([("id", "=", tentative_id)]):
                    id = tentative_id
            except psycopg2.DataError:
                # type error
                raise self._format_import_error(
                    ValueError,
                    _("Invalid database id '%s' for the field '%%(field)s'"),
                    value,
                    {"moreinfo": action},
                ) from None
        elif subfield == "id":
            field_type = _("external id")
            if not self._str_to_boolean(model, field, value)[0]:
                return False, field_type, warnings
            if "." in value:
                xmlid = value
            else:
                xmlid = "%s.%s" % (
                    self._context.get("_import_current_module", ""),
                    value,
                )
            flush(xml_id=xmlid)
            id = self._xmlid_to_record_id(xmlid, RelatedModel)
        elif subfield == ".biko_control_code":
            field_type = _("control code")
            if value == "":
                return False, field_type, warnings
            flush(model=field.comodel_name)
            ids = RelatedModel.search([("biko_control_code", "=", value)])
            if ids:
                if len(ids) > 1:
                    warnings.append(
                        ImportWarning(
                            _(
                                "Found multiple matches for field '%%(field)s' (%d matches)"
                            )
                            % (len(ids))
                        )
                    )
                id = ids[0].id
            else:
                raise self._format_import_error(
                    Exception,
                    _(
                        "Product with control code '%s' was not found. Please create those records manually and try importing again."
                    ),
                    value,
                )
        elif subfield is None:
            field_type = _("name")
            if value == "":
                return False, field_type, warnings
            flush(model=field.comodel_name)
            ids = RelatedModel.name_search(name=value, operator="=")
            if ids:
                if len(ids) > 1:
                    warnings.append(
                        ImportWarning(
                            _(
                                "Found multiple matches for field '%%(field)s' (%d matches)"
                            )
                            % (len(ids))
                        )
                    )
                id, _name = ids[0]
            else:
                name_create_enabled_fields = (
                    self.env.context.get("name_create_enabled_fields") or {}
                )
                if name_create_enabled_fields.get(field.name):
                    try:
                        id, _name = RelatedModel.name_create(name=value)
                    except (Exception, psycopg2.IntegrityError):
                        error_msg = _(
                            "Cannot create new '%s' records from their name alone. Please create those records manually and try importing again.",
                            RelatedModel._description,
                        )
        else:
            raise self._format_import_error(
                Exception, _("Unknown sub-field '%s'"), subfield
            )

        if id is None:
            if error_msg:
                message = _(
                    "No matching record found for %(field_type)s '%(value)s' in field '%%(field)s' and the following error was encountered when we attempted to create one: %(error_message)s"
                )
            else:
                message = _(
                    "No matching record found for %(field_type)s '%(value)s' in field '%%(field)s'"
                )
            raise self._format_import_error(
                ValueError,
                message,
                {"field_type": field_type, "value": value, "error_message": error_msg},
                {"moreinfo": action},
            )
        return id, field_type, warnings
