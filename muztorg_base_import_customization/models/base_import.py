import itertools

from odoo import _, api, models
from odoo.addons.base_import.models.base_import import FIELDS_RECURSION_LIMIT


class Import(models.TransientModel):
    _inherit = "base_import.import"

    @api.model
    def get_fields(self, model, depth=FIELDS_RECURSION_LIMIT):
        Model = self.env[model]
        importable_fields = [
            {
                "id": "id",
                "name": "id",
                "string": _("External ID"),
                "required": False,
                "fields": [],
                "type": "id",
            }
        ]
        if not depth:
            return importable_fields

        model_fields = Model.fields_get()
        blacklist = models.MAGIC_COLUMNS + [Model.CONCURRENCY_CHECK_FIELD]
        for name, field in model_fields.items():
            if name in blacklist:
                continue
            # an empty string means the field is deprecated, @deprecated must
            # be absent or False to mean not-deprecated
            if field.get("deprecated", False) is not False:
                continue
            if field.get("readonly"):
                states = field.get("states")
                if not states:
                    continue
                # states = {state: [(attr, value), (attr2, value2)], state2:...}
                if not any(
                    attr == "readonly" and value is False
                    for attr, value in itertools.chain.from_iterable(states.values())
                ):
                    continue
            field_value = {
                "id": name,
                "name": name,
                "string": field["string"],
                # Y U NO ALWAYS HAS REQUIRED
                "required": bool(field.get("required")),
                "fields": [],
                "type": field["type"],
            }

            if field["type"] in ("many2many", "many2one"):
                field_value["fields"] = [
                    dict(field_value, name="id", string=_("External ID"), type="id"),
                    dict(field_value, name=".id", string=_("Database ID"), type="id"),
                ]

                if field["relation"] in ["product.template", "product.product"]:
                    field_value["fields"].append(
                        {
                            "id": "control_code",
                            "name": ".control_code",
                            "string": _("Control Code"),
                            "required": False,
                            "fields": [],
                            "type": "id",
                        }
                    )
            elif field["type"] == "one2many":
                field_value["fields"] = self.get_fields(
                    field["relation"], depth=depth - 1
                )
                if self.user_has_groups("base.group_no_one"):
                    field_value["fields"].append(
                        {
                            "id": ".id",
                            "name": ".id",
                            "string": _("Database ID"),
                            "required": False,
                            "fields": [],
                            "type": "id",
                        }
                    )

            importable_fields.append(field_value)

        # TODO: cache on model?
        return importable_fields
