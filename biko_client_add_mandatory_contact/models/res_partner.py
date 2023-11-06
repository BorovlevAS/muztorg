import json

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class Partner(models.Model):
    _inherit = "res.partner"

    # служебное поле для связки m2m записей
    biko_parent_id = fields.Many2one("res.partner")
    biko_contact_domain = fields.Char(
        compute="_compute_biko_contact_domain",
        readonly=True,
        store=False,
    )
    biko_contact_person_ids = fields.Many2many(
        comodel_name="res.partner",
        relation="res_partner_contact_person_rel",
        column1="biko_parent_id",
        column2="biko_contact_person_id",
        string="Contact person",
    )

    is_filled_contact_person = fields.Boolean(
        compute="_compute_is_filled_contact_person"
    )

    biko_recipient_ids = fields.Many2many(
        comodel_name="res.partner",
        relation="res_partner_recepient_rel",
        column1="biko_parent_id",
        column2="biko_recipient_ids",
        string="Recipient person",
    )

    biko_payer_id = fields.Many2one(
        comodel_name="res.partner",
        string="Payer person",
    )

    biko_delivery_address_domain = fields.Char(
        compute="_compute_biko_delivery_address_domain",
        readonly=True,
        store=False,
    )

    biko_delivery_address_ids = fields.Many2many(
        comodel_name="res.partner",
        relation="res_partner_delivery_address_rel",
        column1="biko_parent_id",
        column2="biko_delivery_address_ids",
        string="Delivery addresses",
    )

    is_group = fields.Boolean(string="Group of companies", default=False)

    enterprise_code = fields.Char(
        copy=False,
    )

    # обязателен ли код ЕДРПОУ к заполнению
    is_edrpou_mandatory = fields.Boolean(compute="_compute_is_edrpou_mandatory")

    biko_carrier_id = fields.Many2one("delivery.carrier", string="Delivery carrier")

    biko_mobile_compact = fields.Char(
        compute="_compute_biko_mobile_compact", store=True
    )

    biko_1c_phone = fields.Char(string="1C phone")

    def _get_parents(self, parent_ids):
        if not self.parent_id:
            return parent_ids
        parent_ids.append(self.parent_id.id)
        return self.parent_id._get_parents(parent_ids)

    def _compute_biko_contact_domain(self):
        for rec in self:
            parent_ids = rec._get_parents(parent_ids=[rec.id])
            rec.biko_contact_domain = json.dumps(
                [("id", "child_of", parent_ids), ("type", "=", "contact")]
            )

    def _compute_biko_delivery_address_domain(self):
        for rec in self:
            parent_ids = rec._get_parents(parent_ids=[rec.id])
            rec.biko_delivery_address_domain = json.dumps(
                [("id", "child_of", parent_ids), ("type", "!=", "contact")]
            )

    def _compute_is_filled_contact_person(self):
        for rec in self:
            rec.is_filled_contact_person = bool(rec.biko_contact_person_ids)

    @api.depends("vat", "company_id", "enterprise_code")
    def _compute_same_vat_partner_id(self):
        for partner in self:
            # use _origin to deal with onchange()
            partner_id = partner._origin.id
            # active_test = False because if a partner has been deactivated you still want to raise the error,
            # so that you can reactivate it instead of creating a new one, which would loose its history.
            Partner = self.with_context(active_test=False).sudo()
            domain = [
                ("enterprise_code", "=", partner.enterprise_code),
                ("company_id", "in", [False, partner.company_id.id]),
            ]
            if partner_id:
                domain += [
                    ("id", "!=", partner_id),
                    "!",
                    ("id", "child_of", partner_id),
                ]
            partner.same_vat_partner_id = (
                bool(partner.enterprise_code)
                and not partner.parent_id
                and Partner.search(domain, limit=1)
            )

    @api.depends("company_type", "country_id")
    def _compute_is_edrpou_mandatory(self):
        for rec in self:
            if rec.company_type == "person":
                rec.is_edrpou_mandatory = False
            else:
                rec.is_edrpou_mandatory = rec.country_id and rec.country_id.code == "UA"

    # проверяем уникальность клиента по коду ЕДРПОУ
    @api.constrains("enterprise_code")
    def _check_enterprise_code(self):
        for record in self:
            if record.company_type == "person":
                # skip for contact
                continue
            if not record.country_id:
                # skip for foreign company
                continue
            if not record.enterprise_code:
                continue

            Partner = self.with_context(active_test=False).sudo()

            domain = [
                ("enterprise_code", "=", record.enterprise_code),
                ("company_id", "in", [False, record.company_id.id]),
            ]
            partner_id = record._origin.id

            if partner_id:
                domain += [("id", "!=", partner_id)]

            companies = Partner.search(domain).mapped("name")

            if not companies:
                continue

            message = _("Clients with EDRPOU {} is already exists\n").format(
                record.enterprise_code
            )

            for name in companies:
                message += name + "\n"

            raise ValidationError(message)

    @api.depends("mobile")
    def _compute_biko_mobile_compact(self):
        for rec in self:
            if rec.mobile:
                rec.biko_mobile_compact = rec.mobile.replace(" ", "")
            else:
                rec.biko_mobile_compact = False

    def _get_name(self):
        name = super()._get_name()
        partner = self

        if self._context.get("show_mobile"):
            name = _("{name} - mob. {mobile}").format(
                name=name, mobile=partner.mobile or ""
            )

        return name
