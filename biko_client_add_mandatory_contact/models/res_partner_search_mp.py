# monkeypatch - search partner by mobile
import re

from odoo import api
from odoo.osv.expression import get_unaccent_wrapper

from odoo.addons.base.models.res_partner import Partner


class BIKOPartner(Partner):
    @api.model
    def _name_search(
        self, name, args=None, operator="ilike", limit=100, name_get_uid=None
    ):
        self = self.with_user(name_get_uid) if name_get_uid else self
        # as the implementation is in SQL, we force the recompute of fields if necessary
        self.recompute(["display_name"])
        self.flush()
        if args is None:
            args = []
        order_by_rank = self.env.context.get("res_partner_search_mode")
        if (name or order_by_rank) and operator in (
            "=",
            "ilike",
            "=ilike",
            "like",
            "=like",
        ):
            self.check_access_rights("read")
            where_query = self._where_calc(args)
            self._apply_ir_rules(where_query, "read")
            (
                from_clause,
                where_clause,
                where_clause_params,
            ) = where_query.get_sql()
            from_str = from_clause if from_clause else "res_partner"
            where_str = where_clause and (" WHERE %s AND " % where_clause) or " WHERE "

            # search on the name of the contacts and of its company
            search_name = name
            if operator in ("ilike", "like"):
                search_name = "%%%s%%" % name
            if operator in ("=ilike", "=like"):
                operator = operator[1:]

            unaccent = get_unaccent_wrapper(self.env.cr)

            fields = self._get_name_search_order_by_fields()

            # fmt: off
            query = (
                """SELECT res_partner.id
                    FROM {from_str}
                {where} ({email} {operator} {percent}
                    OR {display_name} {operator} {percent}
                    OR {reference} {operator} {percent}
                    OR {mobile} {operator} {percent}
                    OR {enterprise_code} {operator} {percent}
                    OR {vat} {operator} {percent})
                    -- don't panic, trust postgres bitmap
                ORDER BY {fields} {display_name} {operator} {percent} desc,
                        {display_name}
                """.format(  # nosec
                    from_str=from_str,
                    fields=fields,
                    where=where_str,
                    operator=operator,
                    email=unaccent("res_partner.email"),
                    display_name=unaccent("res_partner.display_name"),
                    reference=unaccent("res_partner.ref"),
                    percent=unaccent("%s"),
                    vat=unaccent("res_partner.vat"),
                    mobile=unaccent("res_partner.biko_mobile_compact"),
                    enterprise_code=unaccent("res_partner.enterprise_code"),
                )
            )
            # fmt: on

            where_clause_params += [
                search_name
            ] * 5  # for email / display_name, reference, mobile
            where_clause_params += [
                re.sub(r"[^a-zA-Z0-9\-\.]+", "", search_name) or None
            ]  # for vat
            where_clause_params += [search_name]  # for order by
            if limit:
                query += " limit %s"
                where_clause_params.append(limit)
            self.env.cr.execute(query, where_clause_params)
            return [row[0] for row in self.env.cr.fetchall()]

        return super(Partner, self)._name_search(
            name,
            args,
            operator=operator,
            limit=limit,
            name_get_uid=name_get_uid,
        )


Partner._name_search = BIKOPartner._name_search
